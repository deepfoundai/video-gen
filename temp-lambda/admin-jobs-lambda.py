import json
import boto3
import os
import logging
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
cognito = boto3.client('cognito-idp')

# Get environment variables
JOBS_TABLE = os.environ.get('JOBS_TABLE_NAME', 'Jobs-prod')
S3_BUCKET = os.environ.get('S3_BUCKET', 'deepfound-jobs-prod')
USER_POOL_ID = os.environ.get('USER_POOL_ID', 'us-east-1_q9cVE7WTT')

# Admin user IDs
ADMIN_USER_IDS = [
    "f4c8e4a8-3081-70cd-43f9-ea8a7b407430",  # todd.deshane@gmail.com
    "04d8c4d8-20f1-7000-5cf5-90247ec54b3a",  # todd@theintersecto.com
    "44088418-f0d1-7016-37c9-3bbf83358bb6",  # admin.test@deepfoundai.com
    "5438d488-90d1-70e8-89ae-42946ffbaea7"   # HARVEYCASTRO4@GMAIL.COM
]

def lambda_handler(event, context):
    """
    Admin Jobs API - Handle both list and detail requests
    GET /v1/admin/jobs - List all jobs with filters
    GET /v1/admin/jobs/{jobId} - Get specific job details
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Extract admin user ID from authorizer
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})
    
    # Handle both REST API and HTTP API v2 formats
    claims = authorizer.get("claims", {})
    if not claims:
        jwt_data = authorizer.get("jwt", {})
        claims = jwt_data.get("claims", {})
    
    admin_user_id = claims.get("sub")
    if not admin_user_id:
        return build_response(401, {"error": "Unauthorized"})
    
    # Check if user is admin
    if admin_user_id not in ADMIN_USER_IDS:
        return build_response(403, {"error": "Forbidden - Admin access required"})
    
    # Get path parameters to check if jobId is provided
    path_params = event.get("pathParameters") or {}
    job_id = path_params.get("jobId") or path_params.get("id")
    
    if job_id:
        # Get specific job details
        return get_job_details(job_id, admin_user_id)
    else:
        # List jobs with filters
        return list_jobs(event, admin_user_id)

def list_jobs(event, admin_user_id):
    """List all jobs with optional filters"""
    try:
        table = dynamodb.Table(JOBS_TABLE)
        
        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        status_filter = query_params.get("status")
        user_filter = query_params.get("userId")
        limit = int(query_params.get("limit", "50"))
        
        # Build scan parameters
        scan_params = {
            "Limit": limit,
            "Select": "ALL_ATTRIBUTES"
        }
        
        # Add filters
        filter_expressions = []
        expression_values = {}
        expression_names = {}
        
        if status_filter:
            filter_expressions.append("jobStatus = :status")
            expression_values[":status"] = status_filter
        
        if user_filter:
            # Handle both legacy "user_id" and new "userId" field names
            filter_expressions.append("(#uid = :u OR user_id = :u)")
            expression_values[":u"] = user_filter
            expression_names["#uid"] = "userId"  # userId might be reserved in some contexts
        
        if filter_expressions:
            scan_params["FilterExpression"] = " AND ".join(filter_expressions)
            scan_params["ExpressionAttributeValues"] = expression_values
            if expression_names:
                scan_params["ExpressionAttributeNames"] = expression_names
        
        # Paged scan to ensure we get enough items for proper sorting
        all_jobs = []
        scan_params["Limit"] = 100  # Scan in larger chunks for efficiency
        
        # For small limits, scan more items to ensure we get the newest ones
        # This ensures we don't miss recent jobs due to DynamoDB's random scan order
        min_scan_items = max(limit * 10, 500)  # Scan at least 10x the limit or 500 items
        
        # Keep scanning until we have enough items or reach end of table
        while len(all_jobs) < min_scan_items:
            response = table.scan(**scan_params)
            items = response.get("Items", [])
            all_jobs.extend(items)
            
            # Check if there are more items to scan
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break  # Reached end of table
            scan_params["ExclusiveStartKey"] = last_key
        
        # Sort ALL scanned items by creation time (newest first)
        all_jobs.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        
        # Take only the requested limit after sorting
        jobs = all_jobs[:limit]
        
        # Enrich with user emails
        enriched_jobs = []
        for job in jobs:
            enriched_job = enrich_job_data(job)
            enriched_jobs.append(enriched_job)
        
        # Calculate statistics based on all scanned jobs
        stats = calculate_job_stats(all_jobs)
        
        return build_response(200, {
            "jobs": enriched_jobs,
            "count": len(enriched_jobs),
            "stats": stats,
            "scannedCount": len(all_jobs),
            "hasMore": len(all_jobs) > limit
        })
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return build_response(500, {"error": "Failed to list jobs"})

def get_job_details(job_id, admin_user_id):
    """Get detailed information about a specific job"""
    try:
        table = dynamodb.Table(JOBS_TABLE)
        
        # Get job from DynamoDB
        response = table.get_item(Key={"jobId": job_id})
        
        if "Item" not in response:
            return build_response(404, {"error": "Job not found"})
        
        job = response["Item"]
        
        # Enrich with additional data
        enriched_job = enrich_job_data(job)
        
        # Add admin-specific data
        admin_data = {
            "s3Location": f"s3://{S3_BUCKET}/{job_id}/",
            "logStreamName": job.get("logStreamName"),
            "costEstimate": calculate_job_cost(job),
            "performanceMetrics": get_performance_metrics(job),
            "errorDetails": job.get("errorMessage"),
            "retryCount": job.get("retryCount", 0),
            "adminNotes": job.get("adminNotes", "")
        }
        
        enriched_job["adminData"] = admin_data
        
        # Get related jobs (same user, recent)
        related_jobs = get_related_jobs(job.get("userId"), job_id)
        
        return build_response(200, {
            "job": enriched_job,
            "relatedJobs": related_jobs,
            "retrievedBy": admin_user_id,
            "retrievedAt": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        return build_response(500, {"error": "Failed to get job details"})

def enrich_job_data(job):
    """Enrich job data with user email and other computed fields"""
    enriched = json.loads(json.dumps(job, default=str))  # Handle Decimal
    
    # Get user email
    user_id = job.get("userId")
    if user_id:
        email = get_user_email(user_id)
        enriched["userEmail"] = email
    
    # Calculate duration
    created_at = job.get("createdAt")
    completed_at = job.get("completedAt") or job.get("updatedAt")
    if created_at and completed_at:
        try:
            start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            duration = (end - start).total_seconds()
            enriched["durationSeconds"] = duration
        except:
            pass
    
    # Add display-friendly status
    status = job.get("jobStatus", "UNKNOWN")
    enriched["statusDisplay"] = get_status_display(status)
    
    return enriched

def get_user_email(user_id):
    """Get user email from Cognito"""
    try:
        response = cognito.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=user_id
        )
        
        for attr in response["UserAttributes"]:
            if attr["Name"] == "email":
                return attr["Value"]
        
        return "Unknown"
    except:
        return "Unknown"

def calculate_job_stats(jobs):
    """Calculate statistics across all jobs"""
    stats = {
        "total": len(jobs),
        "byStatus": {},
        "totalCreditsUsed": 0,
        "averageDuration": 0
    }
    
    durations = []
    
    for job in jobs:
        # Count by status
        status = job.get("jobStatus", "UNKNOWN")
        stats["byStatus"][status] = stats["byStatus"].get(status, 0) + 1
        
        # Sum credits
        credits = int(job.get("creditsUsed", 0))
        stats["totalCreditsUsed"] += credits
        
        # Collect durations
        if "durationSeconds" in job:
            durations.append(job["durationSeconds"])
    
    # Calculate average duration
    if durations:
        stats["averageDuration"] = sum(durations) / len(durations)
    
    return stats

def calculate_job_cost(job):
    """Calculate estimated cost of a job"""
    credits_used = int(job.get("creditsUsed", 0))
    cost_per_credit = 0.10  # $0.10 per credit
    
    return {
        "creditsUsed": credits_used,
        "estimatedCost": credits_used * cost_per_credit,
        "currency": "USD"
    }

def get_performance_metrics(job):
    """Get performance metrics for a job"""
    metrics = {
        "queueTime": None,
        "processingTime": None,
        "totalTime": None
    }
    
    # Calculate times if timestamps are available
    created_at = job.get("createdAt")
    started_at = job.get("startedAt") or job.get("updatedAt")
    completed_at = job.get("completedAt")
    
    try:
        if created_at and started_at:
            create_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            metrics["queueTime"] = (start_time - create_time).total_seconds()
        
        if started_at and completed_at:
            start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            complete_time = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            metrics["processingTime"] = (complete_time - start_time).total_seconds()
        
        if created_at and completed_at:
            create_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            complete_time = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            metrics["totalTime"] = (complete_time - create_time).total_seconds()
    except:
        pass
    
    return metrics

def get_related_jobs(user_id, exclude_job_id):
    """Get recent jobs from the same user"""
    if not user_id:
        return []
    
    try:
        table = dynamodb.Table(JOBS_TABLE)
        
        # Query by GSI if available, otherwise scan with filter
        response = table.scan(
            FilterExpression=Attr("userId").eq(user_id) & Attr("jobId").ne(exclude_job_id),
            Limit=5,
            Select="SPECIFIC_ATTRIBUTES",
            ProjectionExpression="jobId, jobStatus, createdAt, prompt"
        )
        
        jobs = response.get("Items", [])
        
        # Sort by creation time
        jobs.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        
        return [json.loads(json.dumps(job, default=str)) for job in jobs[:5]]
        
    except:
        return []

def get_status_display(status):
    """Get display-friendly status text"""
    status_map = {
        "QUEUED": "Waiting in Queue",
        "PROCESSING": "Processing Video",
        "COMPLETED": "Completed Successfully",
        "FAILED": "Failed to Process",
        "CANCELLED": "Cancelled by User"
    }
    return status_map.get(status, status)

def build_response(status_code, body):
    """Build HTTP response"""
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=str)
    }
    
    # CORS is handled by API Gateway
    if not os.environ.get('CORS_HANDLED_BY_GATEWAY'):
        response["headers"]["Access-Control-Allow-Origin"] = "*"
    
    return response
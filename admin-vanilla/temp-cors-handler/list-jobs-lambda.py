import json
import boto3
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key

# Configure allowed origins
ALLOWED_ORIGINS = {
    "https://video.deepfoundai.com",
    "https://admin.deepfoundai.com",
    "http://localhost:5173"
}

# DynamoDB configuration
dynamodb = boto3.resource('dynamodb')
jobs_table = dynamodb.Table('Jobs-prod')

def lambda_handler(event, context):
    """
    List User Jobs API Lambda Function with CORS Support
    GET /v1/jobs
    """
    print(f"Event: {json.dumps(event)}")
    
    # Get the requesting origin
    origin = event.get("headers", {}).get("origin") or event.get("headers", {}).get("Origin")
    print(f"Request origin: {origin}")
    
    # Handle preflight OPTIONS request
    if event.get("httpMethod") == "OPTIONS":
        return handle_preflight(origin)
    
    try:
        # Validate HTTP method
        if event.get("httpMethod") != "GET":
            raise ValueError(f"Method {event.get('httpMethod')} not allowed")
        
        # Get user ID from JWT token
        user_id = get_user_id_from_token(event)
        if not user_id:
            return build_response(401, {"error": "Unauthorized"}, origin)
        
        # Parse query parameters for pagination
        query_params = event.get("queryStringParameters", {}) or {}
        page = int(query_params.get("page", "1"))
        page_size = int(query_params.get("pageSize", "10"))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
        
        # Get jobs for user from DynamoDB
        jobs_response = get_user_jobs(user_id, page, page_size)
        
        # Return jobs list with CORS headers
        return build_response(200, jobs_response, origin)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        error_response = {"error": str(e)}
        status_code = (401 if "Unauthorized" in str(e) else 
                      400 if "Invalid" in str(e) else 500)
        return build_response(status_code, error_response, origin)

def handle_preflight(origin):
    """Handle OPTIONS preflight request"""
    print(f"Handling preflight for origin: {origin}")
    
    if origin in ALLOWED_ORIGINS:
        return {
            "statusCode": 204,
            "headers": {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token",
                "Access-Control-Max-Age": "3600"
            },
            "body": ""
        }
    else:
        print(f"Origin {origin} not in allowed origins: {ALLOWED_ORIGINS}")
        return {
            "statusCode": 403,
            "headers": {},
            "body": json.dumps({"error": "Origin not allowed"})
        }

def build_response(status_code, data, origin):
    """Build API response with CORS headers"""
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(data, default=str)
    }
    
    # Add CORS header if origin is allowed
    if origin in ALLOWED_ORIGINS:
        response["headers"]["Access-Control-Allow-Origin"] = origin
        print(f"Added CORS header for origin: {origin}")
    else:
        print(f"Origin {origin} not allowed, no CORS header added")
    
    print(f"Response: {json.dumps(response)}")
    return response

def get_user_id_from_token(event):
    """Extract user ID from JWT token"""
    try:
        # Check for Authorization header
        auth_header = event.get("headers", {}).get("authorization") or event.get("headers", {}).get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            print("No valid Authorization header found")
            return None
        
        token = auth_header.replace("Bearer ", "")
        print(f"Token found: {token[:20]}...")
        
        # Extract user ID from JWT token payload (without verification for now)
        # In production, you should validate the token signature
        import base64
        import json
        
        try:
            # JWT tokens have 3 parts: header.payload.signature
            payload_part = token.split('.')[1]
            # Add padding if needed for base64 decoding
            padding = len(payload_part) % 4
            if padding:
                payload_part += '=' * (4 - padding)
            
            payload = base64.urlsafe_b64decode(payload_part)
            claims = json.loads(payload)
            
            # Extract user ID from 'sub' (subject) claim
            user_id = claims.get('sub') or claims.get('username')
            if user_id:
                print(f"Extracted user ID: {user_id}")
                return user_id
            else:
                print("No user ID found in token claims")
                return None
                
        except Exception as decode_error:
            print(f"Error decoding JWT token: {str(decode_error)}")
            # Fallback to mock user ID for testing
            return "test-user-123"
        
    except Exception as e:
        print(f"Error extracting user ID: {str(e)}")
        return None

def get_user_jobs(user_id, page, page_size):
    """Get paginated jobs for a specific user"""
    try:
        print(f"Getting jobs for user: {user_id}, page: {page}, page_size: {page_size}")
        
        # Since we don't have a GSI on user_id, we need to scan the table
        # This is not ideal for production with large datasets
        # In production, you should add a GSI with user_id as partition key
        
        # Build scan parameters
        scan_params = {
            'FilterExpression': 'user_id = :user_id',
            'ExpressionAttributeValues': {
                ':user_id': user_id
            }
        }
        
        # Get all jobs for the user (we'll paginate in memory for now)
        all_jobs = []
        last_key = None
        
        while True:
            if last_key:
                scan_params['ExclusiveStartKey'] = last_key
            
            response = jobs_table.scan(**scan_params)
            items = response.get('Items', [])
            all_jobs.extend(items)
            
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
        
        # Sort jobs by creation date (newest first)
        all_jobs.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        # Calculate pagination
        total_jobs = len(all_jobs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get jobs for current page
        page_jobs = all_jobs[start_idx:end_idx]
        
        # Format jobs for response
        formatted_jobs = [format_job_for_list(job) for job in page_jobs]
        
        response = {
            "jobs": formatted_jobs,
            "total": total_jobs,
            "page": page,
            "pageSize": page_size,
            "totalPages": (total_jobs + page_size - 1) // page_size  # Ceiling division
        }
        
        print(f"Found {total_jobs} total jobs, returning {len(formatted_jobs)} for page {page}")
        return response
        
    except Exception as e:
        print(f"Error getting user jobs: {str(e)}")
        # Return empty result on error
        return {
            "jobs": [],
            "total": 0,
            "page": page,
            "pageSize": page_size,
            "totalPages": 0
        }

def format_job_for_list(job):
    """Format job data for list response"""
    try:
        # Provide default timestamp for legacy jobs
        default_timestamp = "2024-01-01T00:00:00Z"
        
        return {
            "jobId": job["jobId"],
            "status": job.get("status", "unknown"),
            "createdAt": job.get("createdAt", default_timestamp),
            "updatedAt": job.get("updatedAt", default_timestamp),
            "prompt": job.get("prompt", "")[:100] + ("..." if len(job.get("prompt", "")) > 100 else ""),  # Truncate for list view
            "duration_seconds": job.get("duration_seconds"),
            "resolution": job.get("resolution"),
            "outputUrl": job.get("outputUrl"),
            "audioUrl": job.get("audioUrl"),  # Include audio URL
            "tier": job.get("tier"),  # Include tier
            "error_message": job.get("error_message")
        }
    except Exception as e:
        print(f"Error formatting job for list: {str(e)}")
        return {
            "jobId": job.get("jobId", "unknown"),
            "status": "error",
            "createdAt": default_timestamp,
            "updatedAt": default_timestamp,
            "prompt": "Error formatting job",
            "duration_seconds": None,
            "resolution": None,
            "outputUrl": None,
            "audioUrl": None,
            "tier": None,
            "error_message": "Format error"
        }
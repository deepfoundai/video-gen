import json
import boto3
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key

# Configure allowed origins
ALLOWED_ORIGINS = {
    "https://admin.deepfoundai.com",
    "http://localhost:5173"
}

# DynamoDB configuration
dynamodb = boto3.resource('dynamodb')
jobs_table = dynamodb.Table('Jobs-prod')

def lambda_handler(event, context):
    """
    Admin Jobs List API Lambda Function - Returns ALL jobs without filtering
    GET /v1/admin/jobs
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
        
        # For admin endpoint, we still check auth but don't filter by user
        # In production, you should verify admin role here
        user_id = get_user_id_from_token(event)
        if not user_id:
            return build_response(401, {"error": "Unauthorized"}, origin)
        
        # Parse query parameters for pagination
        query_params = event.get("queryStringParameters", {}) or {}
        page = int(query_params.get("page", "1"))
        page_size = int(query_params.get("pageSize", "100"))  # Higher default for admin
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 1000:  # Max 1000 for admin
            page_size = 100
        
        # Scan ALL jobs from DynamoDB (no user filter)
        all_jobs = []
        
        scan_params = {
            'Limit': 1000  # DynamoDB max per scan
        }
        
        while True:
            response = jobs_table.scan(**scan_params)
            all_jobs.extend(response.get('Items', []))
            
            # Check if there are more items to scan
            if 'LastEvaluatedKey' not in response:
                break
            scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        
        print(f"Total jobs found: {len(all_jobs)}")
        
        # Sort by creation date (newest first)
        all_jobs.sort(
            key=lambda x: x.get('createdAt', ''), 
            reverse=True
        )
        
        # Apply pagination
        total_jobs = len(all_jobs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_jobs = all_jobs[start_idx:end_idx]
        
        # Calculate statistics
        stats = {
            'total': total_jobs,
            'byStatus': {},
            'byUser': {},
            'byResolution': {},
            'avgDuration': 0
        }
        
        # Aggregate statistics
        total_duration = 0
        duration_count = 0
        
        for job in all_jobs:
            # Status stats
            status = job.get('status', 'UNKNOWN')
            stats['byStatus'][status] = stats['byStatus'].get(status, 0) + 1
            
            # User stats
            user = job.get('user_id', 'UNKNOWN')
            stats['byUser'][user] = stats['byUser'].get(user, 0) + 1
            
            # Resolution stats
            resolution = job.get('resolution', 'UNKNOWN')
            stats['byResolution'][resolution] = stats['byResolution'].get(resolution, 0) + 1
            
            # Duration stats
            duration = job.get('duration_seconds')
            if duration:
                total_duration += int(duration)
                duration_count += 1
        
        if duration_count > 0:
            stats['avgDuration'] = total_duration / duration_count
        
        # Format response with raw data
        response_data = {
            'jobs': format_jobs_list(paginated_jobs),
            'total': total_jobs,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total_jobs + page_size - 1) // page_size,
            'stats': stats,
            'rawCount': len(all_jobs),
            'scanComplete': True
        }
        
        return build_response(200, response_data, origin)
        
    except Exception as e:
        print(f"Error in admin jobs list: {str(e)}")
        import traceback
        traceback.print_exc()
        return build_response(500, {"error": str(e)}, origin)

def handle_preflight(origin):
    """Handle CORS preflight OPTIONS request"""
    if origin in ALLOWED_ORIGINS:
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Max-Age": "600"
            },
            "body": json.dumps({"message": "CORS preflight successful"})
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
                # TODO: Verify user has admin role
                # For now, just check if they're authenticated
                return user_id
            else:
                print("No user ID found in token claims")
                return None
                
        except Exception as decode_error:
            print(f"Error decoding JWT token: {str(decode_error)}")
            return None
        
    except Exception as e:
        print(f"Error extracting user ID: {str(e)}")
        return None

def format_jobs_list(jobs):
    """Format list of jobs for API response - include ALL fields for admin"""
    try:
        formatted_jobs = []
        
        for job in jobs:
            # Include ALL fields from DynamoDB for admin view
            formatted_job = {
                'jobId': job.get('jobId'),
                'user_id': job.get('user_id'),
                'status': job.get('status', 'unknown'),
                'createdAt': job.get('createdAt'),
                'updatedAt': job.get('updatedAt'),
                'outputUrl': job.get('outputUrl'),
                'prompt': job.get('prompt'),
                'duration_seconds': job.get('duration_seconds'),
                'resolution': job.get('resolution'),
                'error_message': job.get('error_message'),
                'provider': job.get('provider'),
                'model': job.get('model'),
                'cost': job.get('cost'),
                'metadata': job.get('metadata'),
                # Include raw DynamoDB item for debugging
                '_raw': job
            }
            
            formatted_jobs.append(formatted_job)
        
        return formatted_jobs
        
    except Exception as e:
        print(f"Error formatting jobs list: {str(e)}")
        return []
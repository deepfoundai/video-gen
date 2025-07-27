import json
import boto3
import os
from datetime import datetime

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
    Get Job Status API Lambda Function with CORS Support
    GET /v1/jobs/{id}
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
        
        # Extract job ID from path parameters
        job_id = get_job_id_from_path(event)
        if not job_id:
            return build_response(400, {"error": "Invalid job ID"}, origin)
        
        # Get job from DynamoDB
        job = get_job_from_db(job_id)
        if not job:
            return build_response(404, {"error": "Job not found"}, origin)
        
        # Verify user owns this job (security check)
        if job.get("user_id") != user_id:
            return build_response(403, {"error": "Access denied"}, origin)
        
        # Return job status with CORS headers
        return build_response(200, format_job_response(job), origin)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        error_response = {"error": str(e)}
        status_code = (401 if "Unauthorized" in str(e) else 
                      400 if "Invalid" in str(e) or "not found" in str(e) else 
                      403 if "Access denied" in str(e) else 500)
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

def get_job_id_from_path(event):
    """Extract job ID from path parameters"""
    try:
        # For API Gateway with path parameters
        path_parameters = event.get("pathParameters", {})
        if path_parameters and "id" in path_parameters:
            return path_parameters["id"]
        
        # For direct Lambda function URL with path
        path = event.get("path", "")
        if path:
            # Extract from path like /v1/jobs/{job_id}
            parts = path.strip("/").split("/")
            if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "jobs":
                return parts[2]
        
        return None
        
    except Exception as e:
        print(f"Error extracting job ID: {str(e)}")
        return None

def get_job_from_db(job_id):
    """Get job details from DynamoDB"""
    try:
        response = jobs_table.get_item(
            Key={'jobId': job_id}
        )
        
        item = response.get('Item')
        if item:
            print(f"Found job: {job_id}")
            return item
        else:
            print(f"Job not found: {job_id}")
            return None
            
    except Exception as e:
        print(f"Error querying DynamoDB: {str(e)}")
        return None

def format_job_response(job):
    """Format job data for API response"""
    try:
        # Provide default timestamp for legacy jobs
        # Use a reasonable default date (e.g., January 1, 2024) for jobs without timestamps
        default_timestamp = "2024-01-01T00:00:00Z"
        
        return {
            "jobId": job["jobId"],
            "status": job.get("status", "unknown"),
            "createdAt": job.get("createdAt", default_timestamp),
            "updatedAt": job.get("updatedAt", default_timestamp),
            "outputUrl": job.get("outputUrl"),
            "audioUrl": job.get("audioUrl"),  # Include audio URL
            "prompt": job.get("prompt"),
            "duration_seconds": job.get("duration_seconds"),
            "resolution": job.get("resolution"),
            "tier": job.get("tier"),  # Include tier
            "error_message": job.get("error_message")
        }
    except Exception as e:
        print(f"Error formatting job response: {str(e)}")
        raise ValueError("Invalid job data format") 
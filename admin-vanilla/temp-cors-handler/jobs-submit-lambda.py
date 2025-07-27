import json
import boto3
import os
import uuid
from datetime import datetime

# Configure allowed origins
ALLOWED_ORIGINS = {
    "https://video.deepfoundai.com",
    "https://admin.deepfoundai.com",
    "http://localhost:5173"
}

def lambda_handler(event, context):
    """
    Jobs Submit API Lambda Function with CORS Support
    POST /jobs
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
        if event.get("httpMethod") != "POST":
            raise ValueError(f"Method {event.get('httpMethod')} not allowed")
        
        # Validate path (skip for Lambda Function URLs)
        path = event.get("path", "")
        if path and not path.endswith("/jobs"):
            raise ValueError(f"Invalid path: {path}")
        
        # Get user ID from JWT token
        user_id = get_user_id_from_token(event)
        if not user_id:
            return build_response(401, {"error": "Unauthorized"}, origin)
        
        # Parse and validate request body
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return build_response(400, {"error": "Invalid JSON in request body"}, origin)
        
        job_request = validate_job_request(body)
        
        # Check user has enough credits
        if not check_user_credits(user_id, 1):  # 1 credit per job
            return build_response(402, {"error": "Insufficient credits"}, origin)
        
        # Create and submit job
        job = create_job(user_id, job_request)
        
        # Return success response with CORS headers
        return build_response(201, {"jobId": job["id"], "status": job["status"]}, origin)
        
    except ValueError as e:
        # Input validation errors should return 400
        print(f"Validation error: {str(e)}")
        return build_response(400, {"error": str(e)}, origin)
    except Exception as e:
        print(f"Error: {str(e)}")
        # CRITICAL: Always include CORS headers on errors
        error_response = {"error": str(e)}
        status_code = (401 if "Unauthorized" in str(e) else 
                      402 if "Insufficient credits" in str(e) else 
                      400 if "Invalid" in str(e) or "Missing" in str(e) else 500)
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

def validate_job_request(body):
    """Validate job submission request"""
    try:
        required_fields = ["prompt", "seconds", "resolution"]
        
        for field in required_fields:
            if field not in body:
                raise ValueError(f"Missing required field: {field}")
        
        prompt = body["prompt"].strip()
        if not prompt:
            raise ValueError("Prompt cannot be empty")
        
        if len(prompt) > 1000:
            raise ValueError("Prompt too long (max 1000 characters)")
        
        seconds = int(body["seconds"])
        if not 2 <= seconds <= 10:
            raise ValueError("Duration must be between 2 and 10 seconds")
        
        resolution = body["resolution"]
        if resolution not in ["720p", "1080p", "4k"]:
            raise ValueError("Invalid resolution")
        
        # For now, only support 720p
        if resolution != "720p":
            raise ValueError("Only 720p resolution is currently supported")
        
        # Build validated request with required fields
        validated_request = {
            "prompt": prompt,
            "seconds": seconds,
            "resolution": resolution
        }
        
        # Include optional fields if present
        if "tier" in body:
            validated_request["tier"] = body["tier"]
        
        if "feature" in body:
            validated_request["feature"] = body["feature"]
        
        return validated_request
        
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Invalid request format: {str(e)}")

def check_user_credits(user_id, required_credits):
    """Check if user has enough credits"""
    try:
        # TODO: Implement actual credit check from DynamoDB
        # For now, return True for testing
        
        print(f"Checking credits for user {user_id}: need {required_credits}")
        
        # Mock credit check - replace with actual database query
        user_credits = 42  # Mock current balance
        
        return user_credits >= required_credits
        
        # Production code would:
        # dynamodb = boto3.resource('dynamodb')
        # table = dynamodb.Table('user-credits')
        # response = table.get_item(Key={'user_id': user_id})
        # current_credits = response.get('Item', {}).get('balance', 0)
        # return current_credits >= required_credits
        
    except Exception as e:
        print(f"Error checking user credits: {str(e)}")
        return False

def create_job(user_id, job_request):
    """Create and submit video generation job"""
    try:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create job data structure matching J-01 specification
        job = {
            "jobId": job_id,  # Primary key for DynamoDB
            "user_id": user_id,
            "prompt": job_request["prompt"],
            "duration_seconds": job_request["seconds"],
            "resolution": job_request["resolution"],
            "status": "QUEUED",  # J-01 specifies "QUEUED" status
            "createdAt": now.isoformat() + "Z",
            "updatedAt": now.isoformat() + "Z",
            "outputUrl": None,  # J-01 field name
            "error_message": None
        }
        
        # Add tier if provided (for model selection)
        if "tier" in job_request:
            job["tier"] = job_request["tier"]
        
        # Add feature flags if provided (e.g., audio)
        if "feature" in job_request:
            job["feature"] = job_request["feature"]
        
        print(f"Created job: {job}")
        
        # Save job to DynamoDB (J-01 Requirement 3)
        save_job_to_db(job)
        
        # TODO: Additional job processing
        # 2. Send to SQS queue for processing
        # 3. Deduct credits from user account
        # 4. Start video generation workflow
        
        # Return job info for API response
        return {
            "id": job_id,
            "status": job["status"]
        }
        
    except Exception as e:
        print(f"Error creating job: {str(e)}")
        raise

def save_job_to_db(job):
    """Save job to DynamoDB Jobs table"""
    try:
        # Initialize DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        jobs_table = dynamodb.Table('Jobs-prod')
        
        # Save job to table
        response = jobs_table.put_item(Item=job)
        print(f"Saved job to DynamoDB: {job['jobId']}")
        return response
        
    except Exception as e:
        print(f"Error saving job to DynamoDB: {str(e)}")
        raise

# Environment variables that should be set in Lambda:
# DYNAMODB_JOBS_TABLE - name of the jobs table
# DYNAMODB_CREDITS_TABLE - name of the credits table
# SQS_QUEUE_URL - URL of the job processing queue
# COGNITO_USER_POOL_ID - for JWT validation
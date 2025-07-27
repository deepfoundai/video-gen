import json
import boto3
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS headers that will be included in ALL responses
# Note: This admin API should allow admin.deepfoundai.com
CORS = {
    "Access-Control-Allow-Origin": "https://admin.deepfoundai.com",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}

def respond(status: int, body: dict | str):
    """Helper function to return consistent responses with CORS headers"""
    return {
        "statusCode": status,
        "headers": CORS,
        "body": json.dumps(body) if isinstance(body, dict) else body,
    }

def lambda_handler(event, context):
    """
    Handle admin overview requests
    """
    try:
        # Log the incoming event for debugging
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Short-circuit OPTIONS requests
        if event.get("httpMethod") == "OPTIONS":
            return respond(200, {"message": "OK"})
        
        # Validate HTTP method
        if event.get("httpMethod") != "GET":
            return respond(405, {"error": f"Method {event.get('httpMethod')} not allowed"})
        
        # Get user ID from authorizer context or JWT token
        user_id = get_user_id_from_token(event)
        if not user_id:
            return respond(401, {"error": "Unauthorized"})
        
        # Check if user has admin permissions
        if not is_admin_user(user_id):
            return respond(403, {"error": "Forbidden - Admin access required"})
        
        # Get admin overview data
        overview_data = get_admin_overview()
        
        logger.info(f"Returning admin overview for user {user_id}")
        return respond(200, overview_data)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return respond(500, {"error": "Internal server error"})

def get_user_id_from_token(event):
    """Extract user ID from JWT token or authorizer context"""
    try:
        # First check authorizer context (if using Cognito Authorizer)
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        claims = authorizer.get("claims", {})
        
        if claims.get("sub"):
            logger.info(f"Found user ID in authorizer claims: {claims['sub']}")
            return claims["sub"]
        
        # Fallback to checking Authorization header
        headers = event.get("headers") or {}
        auth_header = headers.get("authorization") or headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("No valid Authorization header found")
            return None
        
        token = auth_header.replace("Bearer ", "")
        
        # For now, return a mock user ID for testing
        # In production, validate JWT and extract user ID
        # TODO: Implement proper JWT validation with Cognito
        
        logger.info(f"Token found: {token[:20]}...")
        return "test-admin-user"  # Mock admin user ID for testing
        
    except Exception as e:
        logger.error(f"Error extracting user ID: {str(e)}")
        return None

def is_admin_user(user_id):
    """Check if user has admin permissions"""
    try:
        # TODO: Implement actual admin permission check
        # For now, allow access for testing
        
        logger.info(f"Checking admin permissions for user: {user_id}")
        
        # Mock admin check - in production, check user roles in Cognito or database
        admin_users = ["test-admin-user", "admin@example.com"]
        return user_id in admin_users
        
    except Exception as e:
        logger.error(f"Error checking admin permissions: {str(e)}")
        return False

def get_admin_overview():
    """Get admin overview statistics"""
    try:
        # TODO: Implement actual database queries
        # For now, return mock data for testing
        
        logger.info("🔍 LIVE API CALL: Getting admin overview data from Lambda")
        
        # Mock overview data - replace with actual queries
        overview = {
            "total_jobs": 156,
            "jobs_today": 23,
            "jobs_pending": 5,
            "jobs_processing": 2,
            "jobs_completed": 149,
            "jobs_failed": 0,
            "active_users": 42,
            "total_users": 127,
            "credits_consumed_today": 89,
            "total_credits_consumed": 1234,
            "revenue_today": 127.50,
            "revenue_month": 2456.78,
            "system_health": {
                "api_status": "healthy",
                "database_status": "healthy",
                "queue_status": "healthy",
                "storage_status": "healthy"
            },
            "recent_jobs": [
                {
                    "id": "job-001",
                    "user_id": "user-123",
                    "status": "completed",
                    "created_at": "2024-01-15T10:30:00Z",
                    "duration": 45
                },
                {
                    "id": "job-002", 
                    "user_id": "user-456",
                    "status": "processing",
                    "created_at": "2024-01-15T11:15:00Z",
                    "duration": None
                }
            ],
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
        return overview
        
        # Production code would query:
        # - DynamoDB for job statistics
        # - CloudWatch for system health
        # - Payment system for revenue data
        
    except Exception as e:
        logger.error(f"Error getting admin overview: {str(e)}")
        raise

# Environment variables that should be set in Lambda:
# DYNAMODB_JOBS_TABLE - name of the jobs table
# DYNAMODB_USERS_TABLE - name of the users table
# COGNITO_USER_POOL_ID - for JWT validation
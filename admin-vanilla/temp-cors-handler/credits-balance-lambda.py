import json
import boto3
import os
import logging
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS headers that will be included in ALL responses
CORS = {
    "Access-Control-Allow-Origin": "https://video.deepfoundai.com",
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
    Handle credit balance requests
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
        
        # Get credit balance
        balance = get_user_credit_balance(user_id)
        
        # Return success response in format expected by frontend
        response_data = {
            "credits": balance,
            "userId": user_id,
            "currency": "credits",
            "lastUpdated": datetime.utcnow().isoformat(),
            "pendingCharges": 0
        }
        
        logger.info(f"Returning balance for user {user_id}: {balance} credits")
        return respond(200, response_data)
        
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
        return "test-user-123"  # Mock user ID for testing
        
    except Exception as e:
        logger.error(f"Error extracting user ID: {str(e)}")
        return None

def get_user_credit_balance(user_id):
    """Get user's credit balance from DynamoDB"""
    try:
        # TODO: Implement actual DynamoDB lookup
        # For now, return mock data for testing
        
        logger.info(f"Getting balance for user: {user_id}")
        
        # Mock balance - replace with actual DynamoDB query
        # Adding some variation for testing
        import random
        base_balance = 150
        variation = random.randint(-20, 50)
        logger.info(f"LIVE API CALL: Returning mock balance {base_balance + variation} for user {user_id}")
        return base_balance + variation
        
        # Production code would look like:
        # dynamodb = boto3.resource('dynamodb')
        # table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NAME', 'user-credits'))
        # response = table.get_item(Key={'user_id': user_id})
        # return response.get('Item', {}).get('balance', 0)
        
    except Exception as e:
        logger.error(f"Error getting credit balance: {str(e)}")
        return 0

# Environment variables that should be set in Lambda:
# DYNAMODB_TABLE_NAME - name of the credits table
# COGNITO_USER_POOL_ID - for JWT validation
import json
import boto3
import os
from decimal import Decimal
import uuid
from datetime import datetime

# Configure allowed origins
ALLOWED_ORIGINS = {
    "https://video.deepfoundai.com",
    "http://localhost:5173"
}

# Credit pack prices
CREDIT_PACKS = {
    "5": {"credits": 5, "price": 4.99},
    "10": {"credits": 10, "price": 9.99},
    "25": {"credits": 25, "price": 19.99},
    "50": {"credits": 50, "price": 39.99}
}

def lambda_handler(event, context):
    """
    Credits Purchase API Lambda Function with CORS Support
    POST /credits/purchase
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
        
        # Validate path
        path = event.get("path", "")
        if not path.endswith("/credits/purchase"):
            raise ValueError(f"Invalid path: {path}")
        
        # Get user ID from JWT token
        user_id = get_user_id_from_token(event)
        if not user_id:
            return build_response(401, {"error": "Unauthorized"}, origin)
        
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        pack = body.get("pack")
        
        if not pack or pack not in CREDIT_PACKS:
            raise ValueError(f"Invalid credit pack: {pack}")
        
        # Process credit purchase
        result = process_credit_purchase(user_id, pack)
        
        # Return success response with CORS headers
        return build_response(200, result, origin)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # CRITICAL: Always include CORS headers on errors
        error_response = {"error": str(e)}
        status_code = 401 if "Unauthorized" in str(e) else 400 if "Invalid" in str(e) else 500
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
        
        # For now, return a mock user ID for testing
        # In production, validate JWT and extract user ID
        # TODO: Implement proper JWT validation with Cognito
        
        print(f"Token found: {token[:20]}...")
        return "test-user-123"  # Mock user ID for testing
        
    except Exception as e:
        print(f"Error extracting user ID: {str(e)}")
        return None

def process_credit_purchase(user_id, pack):
    """Process credit purchase and update user balance"""
    try:
        pack_info = CREDIT_PACKS[pack]
        credits_to_add = pack_info["credits"]
        price = pack_info["price"]
        
        print(f"Processing purchase for user {user_id}: {credits_to_add} credits for ${price}")
        
        # TODO: Implement actual payment processing with Stripe
        # For now, simulate successful payment
        
        # TODO: Update DynamoDB with new credit balance
        # For now, return mock data
        
        transaction_id = str(uuid.uuid4())
        new_balance = 42 + credits_to_add  # Mock current balance + new credits
        
        # Mock transaction record
        transaction = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "credits": credits_to_add,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
        print(f"Transaction completed: {transaction}")
        
        return {
            "success": True,
            "new_balance": new_balance,
            "transaction_id": transaction_id,
            "credits_purchased": credits_to_add,
            "amount_charged": price
        }
        
        # Production code would:
        # 1. Process payment with Stripe
        # 2. Update DynamoDB user balance
        # 3. Record transaction in transactions table
        # 4. Send confirmation email
        
    except Exception as e:
        print(f"Error processing credit purchase: {str(e)}")
        raise

# Environment variables that should be set in Lambda:
# DYNAMODB_TABLE_NAME - name of the credits table
# STRIPE_SECRET_KEY - for payment processing
# COGNITO_USER_POOL_ID - for JWT validation
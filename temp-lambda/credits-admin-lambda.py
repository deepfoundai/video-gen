import json
import boto3
import os
from decimal import Decimal
import datetime

# Configure allowed origins for admin
ALLOWED_ORIGINS = {
    "https://admin.deepfoundai.com",
    "http://localhost:5173"
}

def lambda_handler(event, context):
    """
    Credits Admin API Lambda Function
    PUT /credits/admin - Set user credits
    GET /credits/admin?userId=xxx - Get specific user credits
    """
    print(f"Event: {json.dumps(event)}")
    
    # Get the requesting origin
    headers = event.get("headers") or {}
    origin = headers.get("origin") or headers.get("Origin")
    print(f"Request origin: {origin}")
    
    # Handle preflight OPTIONS request
    http_method = event.get("httpMethod")
    if not http_method:
        request_context = event.get("requestContext", {})
        http_info = request_context.get("http", {})
        http_method = http_info.get("method")
    
    if http_method == "OPTIONS":
        return handle_preflight(origin)
    
    try:
        # Get admin user ID from authorizer (you should verify they're actually an admin)
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        
        # Handle both REST API and HTTP API v2 formats
        claims = authorizer.get("claims", {})
        if not claims:
            jwt_data = authorizer.get("jwt", {})
            claims = jwt_data.get("claims", {})
        
        admin_user_id = claims.get("sub")
        if not admin_user_id:
            return build_response(401, {"error": "Unauthorized"}, origin)
        
        # TODO: Check if user is actually an admin
        # For now, we'll allow specific user IDs
        ADMIN_USER_IDS = [
            "f4c8e4a8-3081-70cd-43f9-ea8a7b407430",  # todd.deshane@gmail.com
            "04d8c4d8-20f1-7000-5cf5-90247ec54b3a",  # todd@theintersecto.com
            "44088418-f0d1-7016-37c9-3bbf83358bb6"   # admin.test@deepfoundai.com
        ]
        
        if admin_user_id not in ADMIN_USER_IDS:
            return build_response(403, {"error": "Forbidden - Admin access required"}, origin)
        
        if http_method == "GET":
            # Get user credits
            query_params = event.get("queryStringParameters") or {}
            user_id = query_params.get("userId")
            
            if not user_id:
                return build_response(400, {"error": "userId parameter required"}, origin)
            
            balance_info = get_user_balance_info(user_id)
            return build_response(200, balance_info, origin)
            
        elif http_method == "PUT":
            # Set user credits
            body = event.get("body", "{}")
            if event.get("isBase64Encoded"):
                import base64
                body = base64.b64decode(body).decode('utf-8')
            
            try:
                request_data = json.loads(body)
            except:
                return build_response(400, {"error": "Invalid JSON body"}, origin)
            
            user_id = request_data.get("userId")
            new_credits = request_data.get("credits")
            
            if not user_id or new_credits is None:
                return build_response(400, {"error": "userId and credits are required"}, origin)
            
            if not isinstance(new_credits, (int, float)) or new_credits < 0:
                return build_response(400, {"error": "Credits must be a non-negative number"}, origin)
            
            # Update user credits
            result = set_user_credits(user_id, new_credits, admin_user_id)
            return build_response(200, result, origin)
            
        else:
            return build_response(405, {"error": f"Method {http_method} not allowed"}, origin)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return build_response(500, {"error": str(e)}, origin)

def handle_preflight(origin):
    """Handle OPTIONS preflight request"""
    if origin in ALLOWED_ORIGINS:
        return {
            "statusCode": 204,
            "headers": {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, PUT, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "3600"
            },
            "body": ""
        }
    else:
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
    
    if origin in ALLOWED_ORIGINS:
        response["headers"]["Access-Control-Allow-Origin"] = origin
    
    return response

def get_user_balance_info(user_id):
    """Get detailed user balance information"""
    try:
        table_name = os.environ.get('CREDITS_TABLE', 'Credits-prod')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'userId': user_id})
        item = response.get('Item', {})
        
        return {
            "userId": user_id,
            "credits": int(item.get('credits', 0)),
            "email": item.get('email', 'Unknown'),
            "lastUpdated": item.get('lastUpdated', 'Never')
        }
        
    except Exception as e:
        print(f"Error getting user balance: {str(e)}")
        raise

def set_user_credits(user_id, new_credits, admin_id):
    """Set user credits to a specific value"""
    try:
        table_name = os.environ.get('CREDITS_TABLE', 'Credits-prod')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Update or create user record
        response = table.put_item(
            Item={
                'userId': user_id,
                'credits': Decimal(str(new_credits)),
                'lastUpdated': datetime.datetime.utcnow().isoformat() + 'Z',
                'lastModifiedBy': admin_id
            }
        )
        
        return {
            "userId": user_id,
            "credits": int(new_credits),
            "updatedBy": admin_id,
            "timestamp": datetime.datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        print(f"Error setting user credits: {str(e)}")
        raise
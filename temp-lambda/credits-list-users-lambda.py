import json
import boto3
import os
from decimal import Decimal

# Configure allowed origins for admin
ALLOWED_ORIGINS = {
    "https://admin.deepfoundai.com",
    "http://localhost:5173"
}

def lambda_handler(event, context):
    """
    List all users with credits
    GET /credits/admin/users - List all users with credit info
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
        # Verify admin access
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
        
        # Check if user is admin
        ADMIN_USER_IDS = [
            "f4c8e4a8-3081-70cd-43f9-ea8a7b407430",  # todd.deshane@gmail.com
            "04d8c4d8-20f1-7000-5cf5-90247ec54b3a"   # todd@theintersecto.com
        ]
        
        if admin_user_id not in ADMIN_USER_IDS:
            return build_response(403, {"error": "Forbidden - Admin access required"}, origin)
        
        # Get all users from Credits table
        table_name = os.environ.get('CREDITS_TABLE', 'Credits-prod')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Scan all items (in production, consider pagination)
        response = table.scan()
        items = response.get('Items', [])
        
        # Get user details from Cognito
        cognito = boto3.client('cognito-idp')
        user_pool_id = 'us-east-1_q9cVE7WTT'
        
        users = []
        for item in items:
            user_data = {
                "userId": item.get('userId'),
                "credits": int(item.get('credits', 0)),
                "email": item.get('email', 'Unknown'),
                "lastUpdated": item.get('lastUpdated', 'Never'),
                "lastModifiedBy": item.get('lastModifiedBy', 'System')
            }
            
            # Try to get fresh email from Cognito if not in DynamoDB
            if user_data['email'] == 'Unknown' and user_data['userId']:
                try:
                    cognito_user = cognito.admin_get_user(
                        UserPoolId=user_pool_id,
                        Username=user_data['userId']
                    )
                    for attr in cognito_user.get('UserAttributes', []):
                        if attr['Name'] == 'email':
                            user_data['email'] = attr['Value']
                            # Update DynamoDB with email
                            table.update_item(
                                Key={'userId': user_data['userId']},
                                UpdateExpression="SET email = :email",
                                ExpressionAttributeValues={':email': user_data['email']}
                            )
                            break
                except Exception as e:
                    print(f"Could not get user {user_data['userId']} from Cognito: {str(e)}")
            
            users.append(user_data)
        
        # Sort by credits descending
        users.sort(key=lambda x: x['credits'], reverse=True)
        
        return build_response(200, {
            "users": users,
            "total": len(users),
            "totalCredits": sum(u['credits'] for u in users)
        }, origin)
        
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
                "Access-Control-Allow-Methods": "GET, OPTIONS",
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
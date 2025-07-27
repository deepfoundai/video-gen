import json

def lambda_handler(event, context):
    """
    CORS Handler for preflight OPTIONS requests with proper origin validation
    """
    print(f"CORS Handler Event: {json.dumps(event)}")
    
    # Get the requesting origin
    origin = event.get("headers", {}).get("origin") or event.get("headers", {}).get("Origin")
    print(f"Request origin: {origin}")
    
    # Allowed origins
    allowed_origins = [
        "https://admin.deepfoundai.com",
        "https://video.deepfoundai.com",
        "http://localhost:5173"
    ]
    
    # Validate origin
    if origin in allowed_origins:
        allowed_origin = origin
    else:
        # Default to admin site for security
        allowed_origin = "https://admin.deepfoundai.com"
    
    # CORS headers with proper origin
    cors_headers = {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age": "86400"
    }
    
    return {
        "statusCode": 200,
        "headers": cors_headers,
        "body": json.dumps({"message": "CORS preflight successful"})
    }
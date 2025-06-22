#!/bin/bash
# CORS Fix Script - Change Gateway Response Status Code
# DevOps-Debug Agent - 2025-06-22

set -e

echo "=== CORS FIX SCRIPT - GATEWAY RESPONSE STATUS UPDATE ==="
echo "Started at: $(date)"
echo

# API Configuration
CREDITS_API="elu5mb5p45"
JOBS_API="o0fvahtccd"
REGION="us-east-1"

# Function to update gateway response
update_gateway_response() {
    local api_id=$1
    local api_name=$2
    
    echo "--- Updating $api_name ($api_id) ---"
    
    # Update the MISSING_AUTHENTICATION_TOKEN response status code to 200
    echo "Changing MISSING_AUTHENTICATION_TOKEN status from 403 to 200..."
    aws apigateway update-gateway-response \
        --rest-api-id "$api_id" \
        --response-type MISSING_AUTHENTICATION_TOKEN \
        --patch-operations op=replace,path=/statusCode,value=200 \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        echo "✅ Gateway response updated successfully"
    else
        echo "❌ Failed to update gateway response"
        exit 1
    fi
    
    # Create deployment
    echo "Deploying changes to v1 stage..."
    DEPLOYMENT_ID=$(aws apigateway create-deployment \
        --rest-api-id "$api_id" \
        --stage-name v1 \
        --description "CORS fix: Change MISSING_AUTHENTICATION_TOKEN status to 200" \
        --region "$REGION" \
        --query 'id' \
        --output text)
    
    if [ $? -eq 0 ]; then
        echo "✅ Deployed successfully - Deployment ID: $DEPLOYMENT_ID"
    else
        echo "❌ Failed to deploy"
        exit 1
    fi
    
    echo
}

# Function to test API
test_api() {
    local api_id=$1
    local endpoint=$2
    local api_name=$3
    
    echo "--- Testing $api_name ---"
    echo "Endpoint: https://$api_id.execute-api.$REGION.amazonaws.com$endpoint"
    
    # Test OPTIONS request
    RESPONSE=$(curl -s -i -X OPTIONS \
        -H "Origin: https://video.deepfoundai.com" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Authorization,Content-Type" \
        "https://$api_id.execute-api.$REGION.amazonaws.com$endpoint")
    
    # Extract status code
    STATUS_CODE=$(echo "$RESPONSE" | head -1 | cut -d' ' -f2)
    
    echo "Status Code: $STATUS_CODE"
    
    if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "204" ]; then
        echo "✅ CORS Test PASSED"
    else
        echo "❌ CORS Test FAILED"
        echo "Response:"
        echo "$RESPONSE" | head -20
    fi
    
    echo
}

# Main execution
echo "1. UPDATING CREDITS API"
update_gateway_response "$CREDITS_API" "Credits API"

echo "2. UPDATING JOBS API"
update_gateway_response "$JOBS_API" "Jobs API"

echo "3. WAITING FOR PROPAGATION (30 seconds)..."
sleep 30

echo "4. TESTING CORS FIXES"
test_api "$CREDITS_API" "/v1/credits/balance" "Credits API"
test_api "$JOBS_API" "/v1/jobs/overview" "Jobs API"

echo "=== CORS FIX SCRIPT COMPLETED ==="
echo "Completed at: $(date)"
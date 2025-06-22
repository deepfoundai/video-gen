#!/bin/bash
set -e

USER_POOL_ID="us-east-1_q9cVE7WTT"
CLIENT_ID="7paapnr8fbkanimk5bgpriagmg"
TEMP_USERNAME="1418e448-1081-70c8-30bf-94b1a0b7de8c"

echo "🔐 Generating secure smoke test token..." >&2

# Get user status to see if password needs to be changed
USER_STATUS=$(aws cognito-idp admin-get-user \
  --user-pool-id "$USER_POOL_ID" \
  --username "$TEMP_USERNAME" \
  --query 'UserStatus' --output text)

echo "User status: $USER_STATUS" >&2

if [ "$USER_STATUS" = "FORCE_CHANGE_PASSWORD" ]; then
  echo "⚠️  User needs password change. Setting permanent password..." >&2
  
  # Generate a secure random password for the session
  NEW_PASSWORD=$(openssl rand -base64 20)
  
  # Set permanent password
  aws cognito-idp admin-set-user-password \
    --user-pool-id "$USER_POOL_ID" \
    --username "$TEMP_USERNAME" \
    --password "$NEW_PASSWORD" \
    --permanent >&2
  
  echo "✅ Password set successfully" >&2
  
  # Now authenticate with the new password
  JWT_TOKEN=$(aws cognito-idp admin-initiate-auth \
    --user-pool-id "$USER_POOL_ID" \
    --client-id "$CLIENT_ID" \
    --auth-flow ADMIN_NO_SRP_AUTH \
    --auth-parameters USERNAME="$TEMP_USERNAME",PASSWORD="$NEW_PASSWORD" \
    --query 'AuthenticationResult.IdToken' --output text)
    
else
  echo "❌ User status unexpected: $USER_STATUS" >&2
  exit 1
fi

# Output the token (this goes to stdout for capture)
echo "$JWT_TOKEN"

echo "🎯 JWT token generated successfully for smoke testing" >&2
echo "Token expires in 1 hour" >&2 
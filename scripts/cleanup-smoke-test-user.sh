#!/bin/bash
set -e

USER_POOL_ID="us-east-1_q9cVE7WTT"  
TEMP_USERNAME="1418e448-1081-70c8-30bf-94b1a0b7de8c"

echo "🧹 Cleaning up temporary smoke test user..." >&2

# Disable the user
aws cognito-idp admin-disable-user \
  --user-pool-id "$USER_POOL_ID" \
  --username "$TEMP_USERNAME"

echo "✅ Temporary user disabled: $TEMP_USERNAME" >&2
echo "🔒 User can no longer authenticate" >&2

# Optionally delete the user entirely (uncomment if desired)
# aws cognito-idp admin-delete-user \
#   --user-pool-id "$USER_POOL_ID" \
#   --username "$TEMP_USERNAME"
# echo "🗑️  Temporary user deleted entirely" >&2 
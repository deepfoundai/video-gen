# CORS Fix Rollback Guide
**DevOps-Debug Agent**  
**Emergency Rollback Instructions**  
**Estimated Time**: < 2 minutes

## Quick Rollback (If Needed)

If the CORS fix causes any unexpected issues, follow these steps to immediately revert:

### Step 1: Revert Gateway Response Status Codes (30 seconds)

```bash
# Revert Credits API (elu5mb5p45)
aws apigateway update-gateway-response --rest-api-id elu5mb5p45 \
  --response-type MISSING_AUTHENTICATION_TOKEN \
  --patch-operations op=replace,path=/statusCode,value=403 \
  --region us-east-1

aws apigateway update-gateway-response --rest-api-id elu5mb5p45 \
  --response-type DEFAULT_4XX \
  --patch-operations op=replace,path=/statusCode,value=403 \
  --region us-east-1

# Revert Jobs API (o0fvahtccd)
aws apigateway update-gateway-response --rest-api-id o0fvahtccd \
  --response-type MISSING_AUTHENTICATION_TOKEN \
  --patch-operations op=replace,path=/statusCode,value=403 \
  --region us-east-1

aws apigateway update-gateway-response --rest-api-id o0fvahtccd \
  --response-type DEFAULT_4XX \
  --patch-operations op=replace,path=/statusCode,value=403 \
  --region us-east-1
```

### Step 2: Deploy Rollback (30 seconds)

```bash
# Deploy Credits API rollback
aws apigateway create-deployment --rest-api-id elu5mb5p45 \
  --stage-name v1 \
  --description "ROLLBACK: Revert CORS fix - return to 403 status" \
  --region us-east-1

# Deploy Jobs API rollback  
aws apigateway create-deployment --rest-api-id o0fvahtccd \
  --stage-name v1 \
  --description "ROLLBACK: Revert CORS fix - return to 403 status" \
  --region us-east-1
```

### Step 3: Verify Rollback (30 seconds)

```bash
# Test Credits API returns 403 again
curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: https://video.deepfoundai.com" \
  "https://elu5mb5p45.execute-api.us-east-1.amazonaws.com/v1/credits/balance"
# Expected: 403

# Test Jobs API returns 403 again  
curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: https://video.deepfoundai.com" \
  "https://o0fvahtccd.execute-api.us-east-1.amazonaws.com/v1/jobs/overview"
# Expected: 403
```

## What Gets Reverted

| Component | Current (After Fix) | After Rollback |
|-----------|-------------------|----------------|
| MISSING_AUTHENTICATION_TOKEN | HTTP 200 | HTTP 403 |
| DEFAULT_4XX | HTTP 200 | HTTP 403 |
| CORS Headers | ✅ Present | ✅ Present (unchanged) |
| Browser Behavior | ✅ Preflight succeeds | ❌ Preflight fails |

## Complete Rollback Script

Save this as `rollback.sh` and execute if needed:

```bash
#!/bin/bash
# CORS Fix Rollback Script

set -e

echo "=== CORS FIX ROLLBACK INITIATED ==="
echo "Started at: $(date)"

# Revert Credits API
echo "1. Reverting Credits API..."
aws apigateway update-gateway-response --rest-api-id elu5mb5p45 \
  --response-type MISSING_AUTHENTICATION_TOKEN \
  --patch-operations op=replace,path=/statusCode,value=403 \
  --region us-east-1 > /dev/null

aws apigateway update-gateway-response --rest-api-id elu5mb5p45 \
  --response-type DEFAULT_4XX \
  --patch-operations op=replace,path=/statusCode,value=403 \
  --region us-east-1 > /dev/null

aws apigateway create-deployment --rest-api-id elu5mb5p45 \
  --stage-name v1 --description "ROLLBACK: Revert CORS fix" \
  --region us-east-1 > /dev/null

echo "✅ Credits API reverted"

# Revert Jobs API
echo "2. Reverting Jobs API..."
aws apigateway update-gateway-response --rest-api-id o0fvahtccd \
  --response-type MISSING_AUTHENTICATION_TOKEN \
  --patch-operations op=replace,path=/statusCode,value=403 \
  --region us-east-1 > /dev/null

aws apigateway update-gateway-response --rest-api-id o0fvahtccd \
  --response-type DEFAULT_4XX \
  --patch-operations op=replace,path=/statusCode,value=403 \
  --region us-east-1 > /dev/null

aws apigateway create-deployment --rest-api-id o0fvahtccd \
  --stage-name v1 --description "ROLLBACK: Revert CORS fix" \
  --region us-east-1 > /dev/null

echo "✅ Jobs API reverted"

echo "3. Waiting for propagation..."
sleep 10

echo "4. Verifying rollback..."
CREDITS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: https://video.deepfoundai.com" \
  "https://elu5mb5p45.execute-api.us-east-1.amazonaws.com/v1/credits/balance")

JOBS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: https://video.deepfoundai.com" \
  "https://o0fvahtccd.execute-api.us-east-1.amazonaws.com/v1/jobs/overview")

echo "Credits API STATUS: $CREDITS_STATUS (expected: 403)"
echo "Jobs API STATUS: $JOBS_STATUS (expected: 403)"

if [ "$CREDITS_STATUS" = "403" ] && [ "$JOBS_STATUS" = "403" ]; then
    echo "✅ ROLLBACK SUCCESSFUL"
else
    echo "❌ ROLLBACK VERIFICATION FAILED"
    exit 1
fi

echo "=== ROLLBACK COMPLETED ==="
echo "Completed at: $(date)"
```

## When to Consider Rollback

**Immediate rollback if**:
- Real API calls stop working (beyond expected auth errors)
- New 5XX errors appear in CloudWatch
- Unexpected security alerts
- Customer reports of service degradation

**Do NOT rollback for**:
- CORS errors (those are expected to be fixed now)
- Missing authentication errors (those are expected)
- Normal 401/403 responses for unauthenticated requests

## Recovery After Rollback

If rollback is needed, the fix can be re-applied later by:
1. Re-running the original fix commands from `VALIDATION_LOG.md`
2. Or using an updated approach based on lessons learned

## Contact Information

For emergency assistance:
- Check AWS CloudWatch for API Gateway metrics
- Monitor application logs for error patterns
- Escalate to platform engineering if needed
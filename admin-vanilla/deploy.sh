#!/bin/bash

# Simple deployment script for vanilla admin
set -e

echo "🚀 Deploying Vanilla Admin Dashboard"
echo "===================================="

# Add timestamp to force cache refresh
TIMESTAMP=$(date +%s)
cp index.html index.tmp.html
sed -i.bak "s/amazon-cognito-identity.min.js/amazon-cognito-identity.min.js?v=$TIMESTAMP/g" index.tmp.html
mv index.tmp.html index.html
rm -f index.html.bak

# Deploy to S3 admin bucket
echo "Uploading to S3..."
aws s3 cp index.html s3://deepfound-admin-ui-prod/raw-admin.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --metadata-directive REPLACE

# Invalidate CloudFront cache
echo ""
echo "Invalidating CloudFront cache..."
DISTRIBUTION_ID="ERGWO5NT1YNOP"
aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/raw-admin.html" \
    --output json > /tmp/invalidation.json

INVALIDATION_ID=$(cat /tmp/invalidation.json | grep '"Id"' | cut -d'"' -f4)
echo "Invalidation created: $INVALIDATION_ID"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Access at: https://admin.deepfoundai.com/raw-admin.html"
echo ""
echo "Note: CloudFront invalidation may take 1-2 minutes to complete."
echo ""
echo "Test credentials:"
echo "Email: admin.test@deepfoundai.com"
echo "Password: AdminTest123!"
#!/bin/bash

# Deployment script for vanilla admin dashboard
set -e

echo "🚀 Deploying Vanilla Admin Dashboard"
echo "===================================="

# Configuration
S3_BUCKET="deepfound-admin-ui-prod"
CLOUDFRONT_ID="ERGWO5NT1YNOP"

# Deploy main admin page
echo "1. Deploying admin dashboard..."
aws s3 cp index-modular.html "s3://$S3_BUCKET/index.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

# Deploy shared resources
echo "2. Deploying shared resources..."
aws s3 sync shared/ "s3://$S3_BUCKET/shared/" \
    --cache-control "max-age=3600" \
    --exclude "*.bak" \
    --delete

# Deploy page modules
echo "3. Deploying page modules..."
aws s3 sync pages/ "s3://$S3_BUCKET/pages/" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --exclude "*.bak" \
    --delete

# Invalidate CloudFront cache
echo "4. Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_ID \
    --paths "/*" \
    --output json > /tmp/invalidation.json

INVALIDATION_ID=$(cat /tmp/invalidation.json | grep '"Id"' | cut -d'"' -f4)
echo "Invalidation created: $INVALIDATION_ID"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Access at: https://admin.deepfoundai.com/"
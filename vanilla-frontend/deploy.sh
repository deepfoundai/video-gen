#!/bin/bash

# Exit on error
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
S3_BUCKET="video.deepfoundai.com"
AWS_REGION=${AWS_REGION:-"us-east-1"}
AWS_PROFILE=${AWS_PROFILE:-"default"}

echo -e "${GREEN}🚀 Video Generator Vanilla Frontend Deployment${NC}"
echo "================================================"

# Function to check if bucket exists
bucket_exists() {
    aws s3api head-bucket --bucket "$1" --profile ${AWS_PROFILE} 2>/dev/null
    return $?
}

# Function to find CloudFront distribution
find_cloudfront_distribution() {
    aws cloudfront list-distributions \
        --profile ${AWS_PROFILE} \
        --query "DistributionList.Items[?contains(Aliases.Items, '${S3_BUCKET}')].Id" \
        --output text 2>/dev/null || echo ""
}

# Step 1: Check if S3 bucket exists
if bucket_exists "$S3_BUCKET"; then
    echo -e "${GREEN}✅ S3 bucket $S3_BUCKET exists${NC}"
else
    echo -e "${RED}❌ S3 bucket $S3_BUCKET not found${NC}"
    echo -e "${YELLOW}This bucket should already exist as part of the main infrastructure${NC}"
    exit 1
fi

# Step 2: Find CloudFront distribution
echo -e "${GREEN}🔍 Finding CloudFront distribution...${NC}"

# First try to find by alias
CLOUDFRONT_DISTRIBUTION_ID=$(find_cloudfront_distribution)

# If not found by alias, check infrastructure-info.json
if [ -z "$CLOUDFRONT_DISTRIBUTION_ID" ] && [ -f "infrastructure-info.json" ]; then
    CLOUDFRONT_DISTRIBUTION_ID=$(cat infrastructure-info.json | grep '"cloudfront_distribution_id"' | cut -d'"' -f4)
fi

if [ -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo -e "${RED}❌ Could not find CloudFront distribution${NC}"
    echo -e "${YELLOW}Please run ./setup-infrastructure.sh first${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Found CloudFront distribution: $CLOUDFRONT_DISTRIBUTION_ID${NC}"
fi

# Step 3: Build the project
echo -e "${GREEN}📦 Building project...${NC}"
mkdir -p dist
cp index.html dist/
cp error.html dist/

# Step 4: Sync to S3
echo -e "${GREEN}☁️  Uploading to S3...${NC}"

# Upload all files with cache headers
aws s3 sync ./dist s3://${S3_BUCKET} \
    --delete \
    --profile ${AWS_PROFILE} \
    --cache-control "public, max-age=31536000" \
    --metadata-directive REPLACE

# Override cache headers for HTML files (no cache)
aws s3 cp s3://${S3_BUCKET} s3://${S3_BUCKET} \
    --recursive \
    --profile ${AWS_PROFILE} \
    --exclude "*" \
    --include "*.html" \
    --metadata-directive REPLACE \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

# Step 5: Create CloudFront invalidation
echo -e "${GREEN}🔄 Creating CloudFront invalidation...${NC}"

INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${CLOUDFRONT_DISTRIBUTION_ID} \
    --paths "/*" \
    --profile ${AWS_PROFILE} \
    --query 'Invalidation.Id' \
    --output text)

echo -e "${YELLOW}⏳ Waiting for invalidation to complete...${NC}"

# Wait for invalidation to complete
while true; do
    STATUS=$(aws cloudfront get-invalidation \
        --distribution-id ${CLOUDFRONT_DISTRIBUTION_ID} \
        --id ${INVALIDATION_ID} \
        --profile ${AWS_PROFILE} \
        --query 'Invalidation.Status' \
        --output text)
    
    if [ "$STATUS" = "Completed" ]; then
        echo -e "${GREEN}✅ Invalidation completed${NC}"
        break
    fi
    
    echo -n "."
    sleep 5
done

# Step 6: Get CloudFront URL
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
    --id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --profile ${AWS_PROFILE} \
    --query 'Distribution.DomainName' \
    --output text)

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "================================================"
echo -e "${GREEN}🌐 Your application is available at:${NC}"
echo -e "${YELLOW}   https://${S3_BUCKET}${NC}"
echo -e "${YELLOW}   https://${CLOUDFRONT_DOMAIN}${NC}"
echo ""
echo -e "${GREEN}📝 Configuration Summary:${NC}"
echo "   S3 Bucket: $S3_BUCKET"
echo "   CloudFront Distribution: $CLOUDFRONT_DISTRIBUTION_ID"
echo "   Region: $AWS_REGION"
echo ""

# Save deployment info
cat > deployment-info.json <<EOF
{
  "s3_bucket": "$S3_BUCKET",
  "cloudfront_distribution_id": "$CLOUDFRONT_DISTRIBUTION_ID",
  "cloudfront_domain": "$CLOUDFRONT_DOMAIN",
  "custom_domain": "$S3_BUCKET",
  "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "region": "$AWS_REGION"
}
EOF

echo -e "${GREEN}💾 Deployment info saved to deployment-info.json${NC}"
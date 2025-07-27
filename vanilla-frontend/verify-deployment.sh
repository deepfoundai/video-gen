#!/bin/bash

echo "🔍 Verifying Video App Deployment"
echo "================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check CloudFront cache headers
echo -e "\n📡 Checking CloudFront Response Headers..."
HEADERS=$(curl -sI https://video.deepfoundai.com/index.html)

# Check cache-control
CACHE_CONTROL=$(echo "$HEADERS" | grep -i "cache-control:" | cut -d' ' -f2-)
if [[ "$CACHE_CONTROL" == *"no-cache"* ]] || [[ "$CACHE_CONTROL" == *"max-age=0"* ]]; then
    echo -e "${GREEN}✅ Cache-Control: $CACHE_CONTROL${NC}"
else
    echo -e "${RED}❌ Cache-Control: $CACHE_CONTROL${NC}"
fi

# Check content-type
CONTENT_TYPE=$(echo "$HEADERS" | grep -i "content-type:" | cut -d' ' -f2-)
if [[ "$CONTENT_TYPE" == *"text/html"* ]]; then
    echo -e "${GREEN}✅ Content-Type: $CONTENT_TYPE${NC}"
else
    echo -e "${RED}❌ Content-Type: $CONTENT_TYPE${NC}"
fi

# Check CloudFront status
echo -e "\n🌐 CloudFront Distribution Status..."
CF_STATUS=$(aws cloudfront get-distribution --id E2ELC8IZUG70CX --query 'Distribution.Status' --output text 2>/dev/null)
if [[ "$CF_STATUS" == "Deployed" ]]; then
    echo -e "${GREEN}✅ CloudFront Status: $CF_STATUS${NC}"
else
    echo -e "${YELLOW}⏳ CloudFront Status: $CF_STATUS${NC}"
fi

# Check invalidation status
echo -e "\n🔄 Recent Invalidations..."
INVALIDATIONS=$(aws cloudfront list-invalidations --distribution-id E2ELC8IZUG70CX --max-items 3 --query 'InvalidationList.Items[*].[Id,Status,CreateTime]' --output table 2>/dev/null)
echo "$INVALIDATIONS"

# Test page loading
echo -e "\n🧪 Testing Page Loading..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://video.deepfoundai.com/)
if [[ "$RESPONSE" == "200" ]]; then
    echo -e "${GREEN}✅ Main page returns: $RESPONSE${NC}"
else
    echo -e "${RED}❌ Main page returns: $RESPONSE${NC}"
fi

# Check for console errors
echo -e "\n📋 Quick Content Check..."
CONTENT=$(curl -s https://video.deepfoundai.com/ | head -20)
if [[ "$CONTENT" == *"<!DOCTYPE html>"* ]]; then
    echo -e "${GREEN}✅ HTML structure looks correct${NC}"
    
    # Check for our debug messages
    if [[ "$CONTENT" == *"VIDEO APP SCRIPT START"* ]]; then
        echo -e "${GREEN}✅ Debug script found${NC}"
    else
        echo -e "${YELLOW}⚠️  Debug script not found in first 20 lines${NC}"
    fi
else
    echo -e "${RED}❌ HTML structure issue detected${NC}"
fi

echo -e "\n📌 Summary:"
echo "- Main URL: https://video.deepfoundai.com/"
echo "- Debug URL: https://video.deepfoundai.com/debug.html"
echo "- Clean Test: https://video.deepfoundai.com/test-clean.html"
echo -e "\n${YELLOW}Tip: Use Ctrl+Shift+R (Cmd+Shift+R on Mac) to force refresh${NC}"
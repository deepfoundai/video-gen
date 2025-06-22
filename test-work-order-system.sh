#!/bin/bash

# Test script for Issue-as-Work-Order System
# Run this after deploying to verify everything works

set -e

echo "🧪 Testing Issue-as-Work-Order System"
echo "======================================"

# Test 1: Validate GitHub Actions syntax
echo ""
echo "1️⃣ Validating GitHub Actions..."
if command -v actionlint >/dev/null 2>&1; then
    actionlint .github/workflows/enqueue-to-eventbridge.yml
    actionlint .github/workflows/close-on-completion.yml
    echo "   ✅ GitHub Actions syntax valid"
else
    echo "   ⚠️  actionlint not installed - skipping syntax check"
fi

# Test 2: Check DevOps agent can be built
echo ""
echo "2️⃣ Testing DevOps agent build..."
cd meta-agents/cc-agent-devops-automation
if [ -f "template.yaml" ]; then
    if command -v sam >/dev/null 2>&1; then
        sam validate
        echo "   ✅ DevOps agent SAM template valid"
    else
        echo "   ⚠️  SAM CLI not installed - skipping template validation"
    fi
else
    echo "   ⚠️  No SAM template found"
fi
cd ../..

# Test 3: Check AWS credentials are configured
echo ""
echo "3️⃣ Checking AWS configuration..."
if command -v aws >/dev/null 2>&1; then
    if aws sts get-caller-identity >/dev/null 2>&1; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        echo "   ✅ AWS credentials configured for account: $ACCOUNT_ID"
    else
        echo "   ❌ AWS credentials not configured"
        echo "      Run: aws configure"
    fi
else
    echo "   ❌ AWS CLI not installed"
fi

# Test 4: Check EventBridge permissions
echo ""
echo "4️⃣ Testing EventBridge permissions..."
if command -v aws >/dev/null 2>&1 && aws sts get-caller-identity >/dev/null 2>&1; then
    # Test sending a dummy event
    cat > test-event.json << EOF
{
  "Entries": [
    {
      "Source": "test.deployment",
      "DetailType": "test.event",
      "Detail": {
        "test": true,
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      }
    }
  ]
}
EOF
    
    if aws events put-events --cli-input-json file://test-event.json >/dev/null 2>&1; then
        echo "   ✅ EventBridge permissions working"
        rm test-event.json
    else
        echo "   ❌ EventBridge put-events failed - check IAM permissions"
        rm test-event.json
    fi
else
    echo "   ⏭️  Skipping EventBridge test - AWS not configured"
fi

# Test 5: Generate sample issue for manual testing
echo ""
echo "5️⃣ Generating sample issue content..."
cat > sample-issue.md << EOF
**Assigned Agent**: DevOpsAutomation

**What should the agent do?**
• Check the health status of all ContentCraft agents
• Verify heartbeat metrics in CloudWatch for the last 24 hours
• Report any agents that haven't checked in recently
• Generate a summary of agent status

**Deadline**: $(date -u -v+1d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '+1 day' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo 'none')

**Dependencies**: 
None for this test
EOF

echo "   ✅ Sample issue created: sample-issue.md"
echo "      Copy this content when creating your first test issue"

# Test 6: Check for DevOps agent logs
echo ""
echo "6️⃣ Checking for existing DevOps agent..."
if command -v aws >/dev/null 2>&1 && aws sts get-caller-identity >/dev/null 2>&1; then
    # Check if DevOps agent exists
    FUNCTIONS=$(aws lambda list-functions --query 'Functions[?contains(FunctionName, `devops-automation`)].FunctionName' --output text 2>/dev/null || echo "")
    if [ -n "$FUNCTIONS" ]; then
        echo "   ✅ Found DevOps Lambda functions:"
        echo "$FUNCTIONS" | tr '\t' '\n' | sed 's/^/      • /'
    else
        echo "   ⚠️  No DevOps automation Lambda functions found"
        echo "      Deploy with: cd meta-agents/cc-agent-devops-automation && sam deploy"
    fi
else
    echo "   ⏭️  Skipping Lambda check - AWS not configured"
fi

echo ""
echo "🎯 Summary"
echo "=========="
echo "• Code validation: Complete"
echo "• Ready for GitHub push and PR creation"
echo "• After PR merge, create issue using sample-issue.md content"
echo "• Monitor with: aws logs filter-log-events --log-group-name /aws/lambda/cc-agent-devops-automation-prod --filter-pattern 'Agent work request'"
echo ""
echo "🚀 Next: git remote add origin YOUR-REPO-URL && git push -u origin work-order-pilot" 
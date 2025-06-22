# Agent Work-Order System - Deployment Guide

This guide walks you through deploying the Issue-as-Work-Order system in under 1 hour.

## Prerequisites

✅ **GitHub repository** with existing agents  
✅ **AWS account** with EventBridge access  
✅ **GitHub Actions** enabled on the repository  
✅ **DevOps-Automation agent** already deployed  

## Step 1: Set Up GitHub Infrastructure (10 minutes)

### 1.1 Add GitHub Secrets

In your GitHub repository settings → Secrets and variables → Actions:

```bash
# Add these repository secrets:
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>

# GITHUB_TOKEN is automatically provided
```

### 1.2 Verify Files Are Created

The following files should now exist in your repository:

```
.github/
├── ISSUE_TEMPLATE/
│   └── agent-task.yml
└── workflows/
    ├── enqueue-to-eventbridge.yml
    └── close-on-completion.yml
```

### 1.3 Test GitHub Actions

1. Go to **Actions** tab in GitHub
2. You should see the new workflows listed
3. No errors should appear in the workflows

## Step 2: Update DevOps Automation Agent (15 minutes)

### 2.1 Deploy Updated Code

The DevOps Automation agent now includes the new `agentWork` action handler.

```bash
cd meta-agents/cc-agent-devops-automation

# Deploy the updated Lambda
sam build
sam deploy --config-env prod --no-confirm-changeset
```

### 2.2 Verify Deployment

```bash
# Test the health endpoint
aws lambda invoke \
  --function-name cc-agent-devops-automation-prod \
  --payload '{"task_type": "health_check"}' \
  /tmp/response.json

# Check the response
cat /tmp/response.json | jq '.body | fromjson'
```

Should show `agentWork` in the capabilities list.

## Step 3: Configure AWS Permissions (5 minutes)

### 3.1 Update GitHub Actions IAM Policy

Your GitHub Actions need these additional permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "events:PutEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow", 
      "Action": [
        "logs:FilterLogEvents",
        "logs:DescribeLogGroups"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/lambda/cc-agent-*",
        "arn:aws:logs:*:*:log-group:/aws/lambda/cc-agent-*:*"
      ]
    }
  ]
}
```

### 3.2 Test EventBridge Access

```bash
# Test that GitHub Actions can send events
aws events put-events --entries '[{
  "Source": "test.github.actions",
  "DetailType": "test.event", 
  "Detail": "{\"test\": true}"
}]'
```

## Step 4: Create Your First Agent Task (5 minutes)

### 4.1 Test the Issue Template

1. Go to **Issues** → **New Issue**
2. Select **🛠️ Agent Task** template
3. Fill out a simple test task:

```markdown
**Assigned Agent**: DevOpsAutomation

**What should the agent do?**
• Check the health status of all ContentCraft agents
• Verify heartbeat metrics in CloudWatch
• Report any agents that haven't checked in recently

**Deadline**: none

**Dependencies**: 
*Leave empty for this test*
```

4. Click **Submit new issue**

### 4.2 Verify Processing

The issue should automatically get the **Work** and **To-Do** labels.

Check that the GitHub Action ran:
1. Go to **Actions** tab
2. Look for "Enqueue Agent Tasks to EventBridge" workflow run
3. Check the logs for successful EventBridge submission

### 4.3 Monitor Agent Response

```bash
# Check DevOps Automation logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/cc-agent-devops-automation-prod \
  --start-time $(date -d '10 minutes ago' +%s)000 \
  --filter-pattern "Agent work request"
```

You should see logs showing the work was received and processed.

### 4.4 Verify Auto-Close

Within 5-10 minutes, the issue should automatically close with a completion comment.

If it doesn't close automatically, manually trigger:

```bash
gh workflow run close-on-completion.yml
```

## Step 5: Extend Other Agents (Optional, 15 minutes per agent)

### 5.1 Choose an Agent to Extend

For this example, let's extend the **Cost Sentinel** agent:

```bash
cd meta-agents/cc-agent-cost-sentinel/src
```

### 5.2 Add GitHub Issue Handling

Add this to the beginning of your `lambda_handler` function:

```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Check for GitHub issue work events FIRST
    if (event.get('source') == 'github.issues' and 
        event.get('detail-type') == 'cost.sentinel.request'):
        
        detail = event['detail']
        if detail.get('workType') == 'github_issue':
            from github_issue_handler import handle_github_issue_work
            return handle_github_issue_work(detail)
    
    # ... existing cost monitoring logic continues
```

### 5.3 Test Agent Integration

Create a new issue targeting the Cost Sentinel:

```markdown
**Assigned Agent**: CostSentinel

**What should the agent do?**
• Check current budget utilization for AWS and vendors
• Analyze cost trends for the past week  
• Report if we're approaching any alert thresholds

**Deadline**: 2025-06-30T18:00:00Z
```

### 5.4 Deploy and Test

```bash
# Deploy the updated agent
sam build
sam deploy --config-env prod --no-confirm-changeset

# Monitor for the work event processing
aws logs filter-log-events \
  --log-group-name /aws/lambda/cc-agent-cost-sentinel-prod \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --filter-pattern "Processing GitHub issue work"
```

## Step 6: Production Validation (10 minutes)

### 6.1 Create Real Work Tasks

Create a few real tasks that your agents should handle:

**DevOps Task:**
```markdown
**Assigned Agent**: DevOpsAutomation
**What should the agent do?**
• Verify all Lambda functions are healthy
• Check for any CloudFormation stack drift
• Report on resource utilization
```

**Cost Monitoring Task:**
```markdown
**Assigned Agent**: CostSentinel  
**What should the agent do?**
• Generate weekly cost report
• Compare against last month's spending
• Highlight any cost anomalies
```

### 6.2 Monitor System Health

```bash
# Check GitHub Actions are running successfully
gh run list --workflow "Enqueue Agent Tasks to EventBridge" --limit 5

# Check agent processing
aws logs filter-log-events \
  --log-group-name /aws/lambda/cc-agent-devops-automation-prod \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "devops.completed"

# Verify auto-close is working
gh run list --workflow "Close Issues on Agent Completion" --limit 3
```

### 6.3 Set Up Monitoring Dashboard

Consider adding these CloudWatch metrics to your dashboard:

- **GitHub Issues Created** (from GitHub webhook)
- **EventBridge Events Published** (from GitHub Actions)
- **Agent Work Events Processed** (from DevOps Automation)
- **Issues Auto-Closed** (from completion workflow)

## Troubleshooting

### Issue Not Converting to EventBridge Event

**Check:**
- Issue has the `Work` label (should be automatic from template)
- GitHub Action has AWS credentials
- GitHub Action logs for parsing errors

```bash
gh run view <run-id> --log
```

### Agent Not Receiving Work

**Check:**
- EventBridge event was published successfully
- Agent Lambda has EventBridge trigger configured  
- Agent handler includes the new event detection logic

```bash
aws events list-rules --name-prefix "cc-agent"
```

### Issues Not Auto-Closing

**Check:**
- Completion events are being logged properly
- Close workflow has GitHub token permissions
- CloudWatch log group names match your agents

```bash
gh workflow run close-on-completion.yml --verbose
```

### Manual Recovery

If something breaks, you can always:

```bash
# Manually close a specific issue
gh issue close 123 -c "✅ Manually closed after agent completion"

# Manually trigger completion check
gh workflow run close-on-completion.yml -f request_id=issue-123

# Re-send issue to EventBridge
aws events put-events --entries file://manual-event.json
```

## Success Criteria

✅ **Issue Template** creates properly formatted agent tasks  
✅ **GitHub Actions** successfully convert issues to EventBridge events  
✅ **DevOps Agent** routes work to appropriate agents  
✅ **Agents** process work and log completion  
✅ **Auto-Close** workflow detects completion and closes issues  
✅ **Full Audit Trail** visible in GitHub + CloudWatch logs  

## Next Steps

1. **Create more agent tasks** using the template
2. **Set up GitHub Projects** for better task visualization  
3. **Add dependency handling** for complex multi-step work
4. **Integrate with alerts** to auto-create tasks from monitoring
5. **Add metrics collection** for agent work performance

---

## Roll-Back Plan

If you need to disable the system:

1. **Disable GitHub workflows:**
   ```bash
   gh workflow disable "Enqueue Agent Tasks to EventBridge"
   gh workflow disable "Close Issues on Agent Completion"
   ```

2. **Revert DevOps agent:**
   ```bash
   git revert <commit-hash>
   sam deploy --config-env prod
   ```

3. **Remove issue template:**
   ```bash
   rm .github/ISSUE_TEMPLATE/agent-task.yml
   ```

The system is designed to be safe and reversible. Your existing agent functionality will continue to work normally. 
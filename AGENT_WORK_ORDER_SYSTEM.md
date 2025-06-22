# Agent Work-Order System 🛠️

A lightweight "Issue-as-Work-Order" system that leverages GitHub Issues and EventBridge to create a centralized task queue for autonomous agents.

## Overview

This system transforms GitHub Issues into work orders for your autonomous agents. When you create an issue using the **🛠️ Agent Task** template, it automatically:

1. **Converts** the issue into an EventBridge event
2. **Routes** the work to the appropriate agent
3. **Tracks** progress via GitHub issue status
4. **Auto-closes** the issue when the agent completes the task

## Quick Start

### Creating a Task

1. Go to **Issues** → **New Issue**
2. Select **🛠️ Agent Task** template
3. Fill out the form:
   - **Assigned Agent**: Choose from the dropdown
   - **What should the agent do?**: Provide clear, actionable bullets
   - **Deadline**: ISO-8601 format or 'none'
   - **Dependencies**: Link to other issues if needed

### Example Task

```markdown
**Assigned Agent**: DevOpsAutomation

**What should the agent do?**
• Verify admin Lambda is returning 502 errors
• Check CloudWatch logs for error patterns
• Redeploy via deployLambda action if needed
• Monitor deployment success for 10 minutes
• Report back with status and any issues found

**Deadline**: 2025-06-30T18:00:00Z

**Dependencies**: 
• #123 - Database migration must complete first
```

## How It Works

### 1. Issue Creation → EventBridge Event

When you create/edit an issue with the `Work` label:

```yaml
# .github/workflows/enqueue-to-eventbridge.yml
# Automatically parses issue and sends to EventBridge
```

The GitHub Action extracts:
- Agent assignment
- Work specification (base64-encoded)
- Deadline and dependencies
- Issue metadata (number, title, URL)

### 2. Agent Processing

The **DevOpsAutomation** agent receives all `devops.request` events with `action: "agentWork"` and:

- **Routes** work to the appropriate agent
- **Decodes** the base64 specification
- **Publishes** agent-specific events to EventBridge
- **Logs** all routing decisions

### 3. Completion Detection

```yaml
# .github/workflows/close-on-completion.yml  
# Runs every 5 minutes to check for completed tasks
```

The system monitors CloudWatch logs for completion patterns and automatically closes issues with a completion comment.

## Available Agents

| Agent | Capabilities | Event Type |
|-------|--------------|------------|
| **DevOpsAutomation** | Lambda deployment, secret management, infrastructure | `devops.request` |
| **CostSentinel** | Budget monitoring, cost alerts, usage tracking | `cost.sentinel.request` |
| **FalInvoker** | AI model invocation, video generation | `fal.invoker.request` |
| **RoutingManager** | Job routing, queue management | `routing.manager.request` |
| **PromptCurator** | Content generation, trend analysis | `prompt.curator.request` |
| **CreditReconciler** | Billing reconciliation, credit management | `credit.reconciler.request` |
| **DocRegistry** | Documentation updates, registry maintenance | `doc.registry.request` |
| **MrrReporter** | Revenue reporting, metrics calculation | `mrr.reporter.request` |

## Agent Integration

To make your agent work with this system, add EventBridge event handling:

```python
def lambda_handler(event, context):
    # Check for GitHub issue work events
    if (event.get('source') == 'github.issues' and 
        event.get('detail-type') == 'your.agent.request'):
        
        detail = event['detail']
        if detail.get('workType') == 'github_issue':
            return handle_github_issue_work(detail)
    
    # ... existing logic

def handle_github_issue_work(detail):
    issue_number = detail['issueNumber']
    spec = detail['spec']
    deadline = detail['deadline']
    
    try:
        # Process the work specification
        result = process_work_spec(spec)
        
        # Log completion for auto-close system
        print(f"Task completed for issue-{issue_number}: {result}")
        
        return {'status': 'completed', 'result': result}
        
    except Exception as e:
        print(f"Task failed for issue-{issue_number}: {str(e)}")
        raise
```

## DevOps Agent Special Handling

The **DevOpsAutomation** agent has built-in pattern matching for common tasks:

### Lambda Deployment
```markdown
• Deploy the cc-agent-cost-sentinel stack
• Verify deployment succeeded  
• Check CloudWatch metrics after deployment
```
→ Automatically extracts stack name and calls `deployLambda`

### Manual Review
```markdown
• Create new secret for API key
• Update /contentcraft/secrets/new-key
```
→ Flags for manual security review

### Generic Tasks
```markdown  
• Investigate high error rates in prod
• Check all agent heartbeat metrics
• Generate health report
```
→ Acknowledges and queues for manual processing

## Monitoring & Troubleshooting

### Check Issue Processing
```bash
# View GitHub Action logs
gh run list --workflow "Enqueue Agent Tasks to EventBridge"

# Check specific run
gh run view <run-id> --log
```

### Monitor Agent Responses
```bash
# DevOps Automation logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/cc-agent-devops-automation-prod \
  --filter-pattern "Agent work request"

# Check for completion events  
aws logs filter-log-events \
  --log-group-name /aws/lambda/cc-agent-devops-automation-prod \
  --filter-pattern "devops.completed"
```

### Manual Issue Closure
If auto-close fails, manually trigger:

```bash
# Via GitHub Actions
gh workflow run close-on-completion.yml -f request_id=issue-123

# Via API
gh issue close 123 -c "✅ Manually closed after agent completion"
```

## EventBridge Event Formats

### GitHub Issue → DevOps Request
```json
{
  "Source": "github.issues",
  "DetailType": "devops.request", 
  "Detail": {
    "requestId": "issue-123",
    "action": "agentWork",
    "stage": "prod",
    "requestedBy": "GitHubCI",
    "agent": "DevOpsAutomation",
    "payload": {
      "spec": "base64-encoded-specification",
      "deadline": "2025-06-30T18:00:00Z",
      "deps": "base64-encoded-dependencies",
      "issueNumber": "123",
      "issueTitle": "Fix admin Lambda 502 errors",
      "issueUrl": "https://github.com/org/repo/issues/123"
    }
  }
}
```

### Agent-Specific Work Event
```json
{
  "Source": "github.issues",
  "DetailType": "cost.sentinel.request",
  "Detail": {
    "workType": "github_issue",
    "issueNumber": "123", 
    "issueTitle": "Monitor spending limits",
    "issueUrl": "https://github.com/org/repo/issues/123",
    "spec": "• Check if we're over 80% budget\n• Send alert if exceeded",
    "deadline": "2025-06-30T18:00:00Z",
    "dependencies": "",
    "requestedAt": "2025-06-21T12:00:00Z"
  }
}
```

### Completion Event
```json
{
  "Source": "devops.automation",
  "DetailType": "devops.completed",
  "Detail": {
    "requestId": "issue-123",
    "action": "agentWork", 
    "status": "success",
    "result": {
      "agent": "DevOpsAutomation",
      "issueNumber": "123",
      "action": "work_dispatched"
    },
    "latencyMs": 1250,
    "requestedBy": "GitHubCI",
    "timestamp": "2025-06-21T12:00:01Z"
  }
}
```

## Security Considerations

- **Secrets**: DevOps agent flags secret operations for manual review
- **Access**: Only events from `github.issues` source are processed  
- **Audit**: All work requests logged with full traceability
- **Permissions**: GitHub Actions require AWS credentials for EventBridge

## Dependencies & Setup

### GitHub Secrets Required
```bash
# AWS credentials for EventBridge access
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>

# GitHub token for issue management (auto-provided)
GITHUB_TOKEN=<auto-generated>
```

### AWS Permissions
The GitHub Action needs:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow", 
      "Action": ["events:PutEvents"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:FilterLogEvents"],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/cc-agent-*"
    }
  ]
}
```

## Benefits

✅ **Single source of truth** for all agent work  
✅ **Full audit trail** via GitHub + EventBridge + CloudWatch  
✅ **Zero additional infrastructure** - uses existing tools  
✅ **Scales easily** - add new agents by extending the routing table  
✅ **Human oversight** - all tasks visible in GitHub Issues  
✅ **Dependency tracking** - link related work items  
✅ **Automatic cleanup** - completed tasks auto-close  

---

## Next Steps

1. **Create your first agent task** using the issue template
2. **Monitor completion** in CloudWatch logs
3. **Extend agent integration** for your specific agents
4. **Set up Projects view** for better task visualization

The system is designed to grow with your agent ecosystem while maintaining simplicity and reliability. 
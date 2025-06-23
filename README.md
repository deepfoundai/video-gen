# Agent Work Orders

Issue-as-Work-Order system for autonomous agents in the deepfoundai ecosystem.

## How It Works

1. **Create Issue** using the `agent-task` template
2. **Add "Work" label** to trigger the workflow
3. **GitHub Action** parses issue and sends to AWS EventBridge
4. **Agents** receive work orders and execute tasks
5. **Auto-close** when agents publish completion events

## Architecture

```
GitHub Issues → GitHub Actions → EventBridge → Lambda Agents → CloudWatch
```

## Setup

### Required GitHub Secrets

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY` 
- `GH_PAT` (for agent error feedback)

### Supported Agents

- DevOpsAutomation
- CostSentinel
- CreditReconciler
- FalInvoker
- MRRReporter
- PromptCurator
- RoutingManager
- DocRegistry

## Usage

1. Create new issue using `.github/ISSUE_TEMPLATE/agent-task.yml`
2. Select target agent from dropdown
3. Add "Work" label to trigger processing
4. Monitor CloudWatch logs for agent activity
5. Issue auto-closes when work completes

## Example Work Order

See `issue-bodies/J01-revised-formatted.md` for a complete example. 
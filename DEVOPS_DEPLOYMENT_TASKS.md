# DEVOPS DEPLOYMENT TASKS
## Agent: DevOps-Automation
## Priority: IMMEDIATE

### Objective
Deploy Routing-Manager (AGENT-06) to production environment with proper configuration and validation.

### Task List

#### 1. Production Deployment
**Command:**
```bash
cd meta-agents/cc-agent-routing-manager
make deploy STAGE=prod \
  FalQueueUrl=https://sqs.us-east-1.amazonaws.com/…/FalJobQueue-prod \
  ReplicateQueueUrl=https://sqs.us-east-1.amazonaws.com/…/ReplicateJobQueue-prod
```

**Validation Steps:**
- [ ] Deployment completes without errors
- [ ] Lambda function appears in AWS Console
- [ ] Environment variables correctly set
- [ ] VPC/Security group configurations applied

#### 2. Agent Registration
**Command:**
```bash
aws ssm put-parameter \
  --name "/contentcraft/agents/enabled" \
  --value "…,RoutingManager" \
  --overwrite
```

**Validation Steps:**
- [ ] SSM parameter updated successfully
- [ ] Agent appears in enabled agents list
- [ ] No existing agents disrupted

#### 3. Health Verification
**Timeline:** Wait 5 minutes after deployment

**Verification:**
- [ ] Admin Dashboard shows Routing-Manager as **Healthy**
- [ ] No error logs in CloudWatch
- [ ] SQS queue connections working
- [ ] Agent responding to health checks

### Infrastructure Requirements
- Production SQS queue URLs confirmed
- IAM roles and policies in place
- CloudWatch logs group exists
- VPC endpoints configured (if needed)

### Rollback Plan
If deployment fails or health checks don't pass:
1. Revert SSM parameter (remove RoutingManager from enabled list)
2. Delete failed Lambda if necessary
3. Notify coordination team immediately

### Success Criteria
- [ ] All deployment commands execute successfully
- [ ] Health checks pass within 5 minutes
- [ ] Admin Dashboard confirms healthy status
- [ ] Ready for frontend integration

### Post-Deployment Actions
- Update deployment status in coordination plan
- Provide deployment artifacts/logs if requested
- Monitor for first 30 minutes for any anomalies 
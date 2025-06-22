# SMOKE TEST VALIDATION
## All Agents - Validation Protocol
## Use this checklist to validate deployment success

### Objective
Provide a standardized smoke test protocol that all agents can use to verify their work and coordinate final validation.

### Pre-Deployment Checklist
**Before any agent begins work:**
- [ ] All dependencies identified and available
- [ ] Coordination plan acknowledged
- [ ] Rollback procedures understood
- [ ] Communication channels established

### Phase 1: DevOps Validation
**Agent: DevOps-Automation**
**Timeline: Immediate post-deployment**

#### Infrastructure Smoke Tests
```bash
# 1. Verify Lambda deployment
aws lambda get-function --function-name RoutingManager-prod

# 2. Check environment variables
aws lambda get-function-configuration --function-name RoutingManager-prod | jq '.Environment.Variables'

# 3. Test SQS connectivity
aws sqs get-queue-attributes --queue-url FalJobQueue-prod
aws sqs get-queue-attributes --queue-url ReplicateJobQueue-prod

# 4. Verify SSM parameter
aws ssm get-parameter --name "/contentcraft/agents/enabled"
```

#### Health Check Validation
- [ ] Lambda function returns 200 on health endpoint
- [ ] CloudWatch logs show startup messages
- [ ] No error logs in first 5 minutes
- [ ] Admin Dashboard shows "Healthy" status
- [ ] SQS queue permissions working

**Expected Results:**
```json
{
  "status": "healthy",
  "agent": "RoutingManager",
  "version": "1.0.x",
  "queues": {
    "fal": "connected",
    "replicate": "connected"
  }
}
```

### Phase 2: Frontend Validation
**Agent: Frontend-Integration**
**Timeline: Parallel with DevOps**

#### UI Smoke Tests
**Test Cases:**
1. **Basic Job Submission**
   ```json
   // Submit this payload via UI
   {
     "provider": "auto",
     "durationSec": 5,
     "resolution": "720p",
     "prompt": "Test routing smoke test"
   }
   ```
   - [ ] Payload successfully sent
   - [ ] UI shows "routing..." or similar loading state
   - [ ] Job appears in queue/tracking system

2. **Fail-Soft Validation**
   ```json
   // Test unsupported job
   {
     "provider": "auto", 
     "durationSec": 15, // >10 seconds
     "resolution": "1080p", // >720p
     "prompt": "Test fail-soft message"
   }
   ```
   - [ ] User sees friendly error message
   - [ ] No hard errors or crashes
   - [ ] Message mentions current limitations

#### Visual Validation
- [ ] All existing UI components render correctly
- [ ] No console errors in browser
- [ ] Loading states display appropriately
- [ ] Error messages are user-friendly

### Phase 3: End-to-End Integration Test
**All Agents Coordinate**
**Timeline: After both Phase 1 & 2 complete**

#### Integration Test Scenario
```
Test Case: Complete Video Generation Flow
1. User submits 8-second, 720p video via UI
2. Frontend sends "auto" provider request
3. RoutingManager receives and routes to Fal
4. Job processes successfully
5. User receives completed video
```

**Validation Steps:**
- [ ] Job submitted via updated UI
- [ ] RoutingManager logs show routing decision
- [ ] Job routed to correct provider (Fal)
- [ ] Video generation completes successfully
- [ ] User sees completed video in UI
- [ ] No errors in any system logs

### Phase 4: Monitoring Validation
**Agent: Monitoring-Agent**
**Timeline: Post-deployment (after 15 minutes)**

#### Metrics Validation
- [ ] `RoutingManager/Routed` metric shows test job
- [ ] `RoutingManager/Latency` metric recorded
- [ ] CloudWatch dashboard displays data
- [ ] No false alerts triggered

#### Alert Testing
```bash
# Simulate DLQ message (if safe to do)
# OR verify alert configuration without triggering
aws cloudwatch describe-alarms --alarm-names "RoutingManager-DLQ-Alert"
```

### Final Validation Checklist
**All agents must confirm:**

#### System Health
- [ ] All services responding normally
- [ ] No error spikes in monitoring
- [ ] Queue depths normal
- [ ] Response times acceptable

#### User Experience
- [ ] UI responsive and functional
- [ ] Error messages helpful and clear
- [ ] Job submission flow smooth
- [ ] Results display correctly

#### Operational Readiness
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Rollback procedures tested
- [ ] Team notifications sent

### Success Criteria Screenshots
**Required Evidence:**
1. **Admin Dashboard** - showing RoutingManager as Healthy
2. **CloudWatch Metrics** - showing routing activity
3. **UI Test** - successful job with "auto" provider
4. **Logs** - clean startup and operation logs

### Escalation Triggers
**Immediate escalation if:**
- Any health check fails
- UI shows hard errors
- Monitoring setup incomplete
- End-to-end test fails

### Sign-Off Protocol
**Each agent must confirm:**
```markdown
Agent: [Agent Name]
Status: ✅ PASSED / ❌ FAILED
Timestamp: [ISO timestamp]
Notes: [Any observations or concerns]
Evidence: [Links to screenshots/logs]
```

**Final Coordinator Sign-Off:**
Only after all agents confirm PASSED status:
```markdown
Deployment Status: APPROVED FOR PRODUCTION TRAFFIC
Coordinator: [Name]
Timestamp: [ISO timestamp]
Next Steps: Begin user traffic monitoring
``` 
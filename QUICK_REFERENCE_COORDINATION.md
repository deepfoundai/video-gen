# QUICK REFERENCE - AGENT COORDINATION
## Routing-Manager Production Deployment

### 📋 Task Distribution Summary

| Agent | File | Priority | Estimated Time | Dependencies |
|-------|------|----------|----------------|--------------|
| **DevOps-Automation** | `DEVOPS_DEPLOYMENT_TASKS.md` | IMMEDIATE | 30-45 min | None |
| **Frontend-Integration** | `FRONTEND_INTEGRATION_TASKS.md` | HIGH | 2-3 hours | Backend APIs deployed |
| **Monitoring-Agent** | `MONITORING_ALERTING_TASKS.md` | POST-DEPLOY | 30-45 min | Frontend + Backend complete |
| **Product-Planning** | `PRODUCT_PLANNING_TASKS.md` | CONTINUOUS | Ongoing | Full integration success |

### 🚀 Execution Sequence

#### **Phase 1: Backend Deployment (Start Immediately)**
```
DevOps-Automation
       ↓
   Deploy Lambda (Routing-Manager)
   Configure SSM
   Verify Health & APIs
       ↓
   ✅ Backend Ready
```

#### **Phase 2: Frontend Integration**
```
Frontend-Integration (after backend ready)
                    ↓
    Complete Auth Flow (Cognito)
    Build API Client Layer
    Create Dashboard/Jobs/Gallery Pages
    Add Cypress E2E Tests
                    ↓
              ✅ Frontend Ready
```

#### **Phase 3: Integration Validation**
```
Both backend + frontend complete → Run end-to-end smoke test
                                ↓
                          ✅ Integration Success
                                ↓
                       Enable Monitoring-Agent
```

#### **Phase 4: Production Ready**
```
Monitoring-Agent → Set up alerts & dashboards
                ↓
       ✅ All systems monitored
                ↓
      Product-Planning → Next increment planning
```

### 📞 Communication Protocol

#### **Status Updates (Required)**
- **Every 15 minutes** during Phase 1
- **Immediately** on completion or blocking issues
- **Use standardized format:**
  ```
  Agent: [Name]
  Status: IN_PROGRESS | BLOCKED | COMPLETE
  ETA: [timestamp if in progress]
  Issues: [any problems or concerns]
  ```

#### **Escalation Triggers**
- Any task blocked >30 minutes
- Health checks failing
- Integration test failures
- Unexpected errors

### 🔧 Quick Commands Reference

#### **DevOps-Automation**
```bash
# Deploy
cd meta-agents/cc-agent-routing-manager && make deploy STAGE=prod

# Register
aws ssm put-parameter --name "/contentcraft/agents/enabled" --value "...,RoutingManager" --overwrite

# Verify
aws lambda get-function --function-name RoutingManager-prod
```

#### **Frontend-Integration**
```javascript
// Change payload from:
{ "provider": "fal", ... }
// To:
{ "provider": "auto", ... }
```

#### **Monitoring-Agent**
```bash
# Verify metrics
aws cloudwatch list-metrics --namespace RoutingManager

# Test alerts
aws cloudwatch describe-alarms --alarm-names "RoutingManager-DLQ-Alert"
```

### ✅ Success Validation Checklist

#### **Critical Success Criteria (All must pass)**
- [ ] RoutingManager Lambda deployed and healthy
- [ ] Admin Dashboard shows "Healthy" status  
- [ ] Frontend submits jobs with "provider": "auto"
- [ ] End-to-end test job completes successfully
- [ ] Monitoring alerts configured and tested
- [ ] No errors in any system logs

#### **Evidence Required**
1. Screenshot of Admin Dashboard (healthy status)
2. Sample successful job with auto-routing
3. CloudWatch metrics showing activity
4. Clean log files from deployment

### 🚨 Emergency Procedures

#### **If Deployment Fails**
1. **Immediate:** Revert SSM parameter
2. **Quick:** Notify all agents to halt
3. **Analysis:** Capture logs and error details
4. **Recovery:** Execute rollback procedures

#### **If Integration Test Fails**
1. **Frontend:** Revert to "fal" provider
2. **Backend:** Disable RoutingManager in SSM
3. **Investigation:** Debug with isolated tests
4. **Communication:** Update coordination plan

### 📊 Final Sign-Off Requirements

**Each agent must provide:**
```markdown
Agent: [Name]
Status: ✅ PASSED
Completion Time: [timestamp]
Evidence Links: [screenshots/logs]
Ready for Production: YES
```

**Coordinator Final Approval:**
Only after ALL agents confirm success:
```markdown
🎉 DEPLOYMENT APPROVED FOR PRODUCTION TRAFFIC
Coordinator: [Name]
Go-Live Time: [timestamp]
Monitoring: ACTIVE
Next Milestone: User traffic analysis
```

---
**📁 All task files ready for distribution to respective agents**
**🤝 Coordination complete - Ready to execute deployment** 
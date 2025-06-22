# A-02: Normalize CORS Runbook into Repo

## Agent Assignment
DevOpsAutomation

## Priority
Low

## Work Specification

### Overview
Create a standardized CORS troubleshooting guide and validation process to prevent future CORS issues across all APIs and services.

### Problem Statement
- CORS issues recur across different services
- No centralized troubleshooting guide
- No automated validation in CI/CD pipeline
- Knowledge scattered across multiple documentation sources

### Requirements

#### 1. CORS Guide Documentation
- **File:** `/docs/CORS_GUIDE.md`
- **Content:** 5-point troubleshooting checklist
- **Format:** Step-by-step procedures with examples
- **Scope:** Cover API Gateway, Lambda, and frontend integration

#### 2. CORS Checklist
1. **Headers Validation**
   - Access-Control-Allow-Origin set to specific domains (not *)
   - Access-Control-Allow-Methods includes required HTTP methods
   - Access-Control-Allow-Headers includes Content-Type, Authorization
   - Access-Control-Max-Age set appropriately

2. **OPTIONS Endpoint**
   - OPTIONS preflight request returns 200 status
   - No authentication required for OPTIONS
   - Proper headers in OPTIONS response
   - Fast response time (<200ms)

3. **API Gateway Configuration**
   - CORS enabled on all required resources
   - Integration response headers configured
   - Method response headers configured
   - Binary media types if needed

4. **Lambda Response Format**
   - Proper statusCode (200, 201, etc.)
   - Headers object includes CORS headers
   - Body is JSON string, not object
   - Content-Type header set correctly

5. **Frontend Integration**
   - Credentials: 'include' if using auth
   - Request headers match allowed headers
   - Content-Type matches server expectations
   - Error handling for CORS failures

#### 3. CI Validation Step
- **Script:** `scripts/validate-cors.sh`
- **Function:** Test OPTIONS requests to all public endpoints
- **Integration:** Add to GitHub Actions workflow
- **Failure Condition:** Any OPTIONS request returns ≠ 200

#### 4. Automated Testing
- Test all current API endpoints for CORS compliance
- Validate from frontend domains (dev, staging, prod)
- Include in existing test suites
- Document any exceptions or special cases

### Deliverables

#### 1. Documentation
- `/docs/CORS_GUIDE.md` - Complete troubleshooting guide
- Update existing API documentation with CORS sections
- Add CORS requirements to deployment checklists
- Include examples for common frameworks (Svelte, React)

#### 2. Validation Script
- Automated CORS testing script
- Integration with CI/CD pipeline
- Clear error messages and remediation steps
- Support for different environments (dev/prod)

#### 3. Implementation Fixes
- Fix any discovered CORS issues during validation
- Standardize CORS headers across all services
- Update existing APIs to match best practices
- Document any service-specific requirements

### Acceptance Criteria
- [ ] `/docs/CORS_GUIDE.md` created with 5-point checklist
- [ ] CORS validation script created and working
- [ ] CI step added that fails if OPTIONS returns ≠ 200
- [ ] All current APIs pass CORS validation
- [ ] Documentation includes practical examples
- [ ] Script tests multiple frontend domains
- [ ] Guide covers troubleshooting common issues
- [ ] Validation integrated into deployment process

### Dependencies
None

### Deadline
2024-06-27 (5 days)

### Notes
This is preventive maintenance to avoid recurring CORS issues. Focus on practical, actionable guidance that developers can follow easily. 
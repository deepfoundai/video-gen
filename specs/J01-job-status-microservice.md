# J-01: Build Job-Status Micro-service

## Agent Assignment
DevOpsAutomation

## Priority
High

## Work Specification

### Overview
Build a new microservice to track job status and provide real-time updates to the frontend. This will replace the current hard-coded polling mechanism with a proper status tracking system.

### Requirements

#### 1. DynamoDB Table
- **Table Name:** `Jobs-${stage}` (prod/dev)
- **Primary Key:** `jobId` (String)
- **TTL:** 30 days automatic cleanup
- **Attributes:**
  - `jobId` - Unique identifier
  - `status` - QUEUED | PROCESSING | COMPLETED | FAILED
  - `createdAt` - ISO timestamp
  - `updatedAt` - ISO timestamp  
  - `userId` - User identifier
  - `ttl` - TTL timestamp for auto-cleanup

#### 2. Lambda Function
- **Function Name:** `GetJobFn-${stage}`
- **Runtime:** Python 3.12
- **Memory:** 256MB
- **Timeout:** 30s
- **Environment Variables:**
  - `JOBS_TABLE_NAME`
  - `STAGE`

#### 3. API Endpoints
- **GET `/v1/jobs/{id}`**
  - Authentication: Cognito JWT required
  - Response: `{"jobId": "...", "status": "...", "createdAt": "...", "updatedAt": "..."}`
  - Error handling: 404 for not found, 401 for unauthorized

- **OPTIONS `/v1/jobs/{id}`**
  - No authentication required (CORS preflight)
  - Proper CORS headers for frontend domains

#### 4. Integration
- Add to existing Jobs API Gateway
- No separate API Gateway needed
- Use existing Cognito authorizer
- Maintain consistent error response format

#### 5. Monitoring
- **CloudWatch Metric:** `JobStatus/Latency`
- **CloudWatch Logs:** Structured JSON logging
- **Alarms:** >5s response time, >5% error rate

#### 6. Testing
- SAM template validation
- Unit tests for Lambda function
- Integration tests for DynamoDB operations
- CORS validation tests

### Acceptance Criteria
- [ ] DynamoDB table deployed with proper indexes and TTL
- [ ] Lambda function deployed and responding to API calls
- [ ] GET endpoint returns proper job status with authentication
- [ ] OPTIONS endpoint works without authentication for CORS
- [ ] CloudWatch metrics being published
- [ ] All tests passing
- [ ] SAM template validates successfully
- [ ] Integration with existing API Gateway complete

### Dependencies
None - this is foundational infrastructure

### Deadline
2024-06-25 (3 days)

### Notes
This microservice will be consumed by J-02 (FalInvoker) and J-03 (Frontend) so prioritize completion. 
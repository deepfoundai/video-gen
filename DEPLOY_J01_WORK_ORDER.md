# J-01 Job Status Implementation Work Order

## Work Order Details

| Field | Value |
|-------|-------|
| **Target Agent** | DevOpsAutomation |
| **Environment** | prod |
| **Deadline (UTC)** | 2025-06-28T23:59 |

## Work Specification

### 📐 What should the agent do?

Build *incremental* Job-Status support **inside the existing Jobs API** (no parallel micro-service yet).

1. **DynamoDB Table**
   * Create table `Jobs-${stage}` (stage = prod)
   * Primary Key: `jobId` (string)
   * Attributes: status, createdAt, updatedAt, outputUrl
   * GSI for status-based queries if needed

2. **Lambda Function - GetJobFn**
   * Runtime: Python 3.12, Memory: 256 MB
   * Handler: GET `/v1/jobs/{id}` endpoint
   * API Gateway REST integration with Cognito authentication
   * OPTIONS mock for CORS (admin + video domains)
   * Return job status, metadata, and progress

3. **Jobs-Submit Lambda Patch**
   * Modify existing job submission Lambda
   * Persist new item `{jobId, status:"QUEUED", createdAt, updatedAt}` to DynamoDB table
   * Ensure backward compatibility with existing functionality

4. **SAM Template Updates**
   * Extend existing `jobs-api` CloudFormation stack
   * **Do NOT create a new REST API**
   * Add DynamoDB table resource
   * Add GetJobFn Lambda resource
   * Add IAM roles and policies
   * Add API Gateway method integration

5. **Unit Tests**
   * Test coverage ≥ 80%
   * Test DynamoDB read/write operations
   * Test API Gateway integration
   * Test error handling and edge cases

### Done when
* `curl GET /v1/jobs/{id}` returns 200 JSON with correct status fields
* Frontend dashboard can query job status (polling to be wired by frontend team)
* All tests pass with ≥ 80% coverage
* CloudFormation deployment succeeds

## Dependencies

none

## Context & Notes

### 🔐 Security / IAM Requirements
* Grant GetJobFn minimal `dynamodb:GetItem` permission on `Jobs-${stage}` table only
* Use existing Cognito User Pool for authentication
* Maintain existing CORS configuration for admin.deepfoundai.com and video.deepfoundai.com

### 📎 Technical Context
* Jobs API is at `o0fvahtccd.execute-api.us-east-1.amazonaws.com`
* Existing Lambdas are in `frontend/backend` directory
* Current API uses REST API Gateway (not HTTP API)
* Future work will migrate to formal SAM repository structure

### 🚧 Implementation Notes
* **Phase 1 is additive** - do not break existing functionality
* Use existing CloudFormation stack naming conventions
* Follow existing code patterns and directory structure
* Ensure minimal disruption to current job submission flow

### 📊 Expected API Response Format
```json
{
  "jobId": "job_abc123",
  "status": "QUEUED|PROCESSING|COMPLETED|FAILED",
  "createdAt": "2025-06-23T12:00:00Z",
  "updatedAt": "2025-06-23T12:05:00Z",
  "outputUrl": "https://example.com/output.mp4"
}
``` 
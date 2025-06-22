# J-02: Emit Job Records from FalInvoker

## Agent Assignment
FalInvoker

## Priority
High

## Work Specification

### Overview
Integrate the FalInvoker agent with the new Job-Status microservice to emit job status records throughout the video generation lifecycle.

### Requirements

#### 1. Job Status Integration
- **On Job Queue:** Write `{jobId, status: 'QUEUED', createdAt, userId}` to DynamoDB
- **On Processing Start:** Update status to `'PROCESSING'` with `updatedAt`
- **On Completion:** Update status to `'COMPLETED'` with `updatedAt` and result metadata
- **On Failure:** Update status to `'FAILED'` with `updatedAt` and error details

#### 2. DynamoDB Operations
- Use existing AWS SDK patterns from other agents
- Implement proper error handling and retries
- Include TTL calculation (30 days from creation)
- Add structured logging for all DynamoDB operations

#### 3. Job ID Management
- Extract `jobId` from incoming EventBridge events
- If no `jobId` provided, generate UUID4
- Include `jobId` in all downstream processing logs
- Pass `jobId` to Fal API requests where possible

#### 4. Status Definitions
- **QUEUED:** Job received and validated, waiting for processing
- **PROCESSING:** Fal API request sent, waiting for completion
- **COMPLETED:** Successful result received from Fal API
- **FAILED:** Error occurred (validation, API failure, timeout, etc.)

#### 5. Error Handling
- DynamoDB write failures should not block job processing
- Log all status update failures to CloudWatch
- Include retry logic with exponential backoff
- Maintain existing error handling for Fal API

#### 6. Metadata Enhancement
- Store user context from incoming events
- Record Fal API response times
- Track processing metrics for monitoring
- Include error details for failed jobs

### Acceptance Criteria
- [ ] Jobs table updated when FalInvoker receives work
- [ ] Status transitions through QUEUED → PROCESSING → COMPLETED/FAILED
- [ ] All job records include proper TTL for cleanup
- [ ] Error handling doesn't impact existing Fal API workflow
- [ ] CloudWatch logs include jobId in all entries
- [ ] Integration tests verify status updates
- [ ] Existing functionality remains unchanged
- [ ] Performance impact <100ms per job

### Dependencies
**Depends on J-01** - Requires Job-Status microservice deployment

### Deadline
2024-06-26 (4 days)

### Notes
This integration should be transparent to existing video generation workflow. Focus on reliability over features - job processing is more important than status tracking. 
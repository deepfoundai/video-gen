### 🗂  Work Order

| Field | Value |
|-------|-------|
| **agent** | DevOpsAutomation |
| **stage** | prod |
| **requestId** | J-01-2025-06-25 |
| **deps** | — |
| **deadline (UTC)** | 2025-06-28T00:00 |

---

### 📐 What should the agent do?
Build *incremental* Job-Status support **inside the existing Jobs API** (no parallel micro-service yet).

1. **DynamoDB**
   * Table `Jobs-${stage}`  
     * PK =`jobId` (string)  
     * status, createdAt, updatedAt, outputUrl
2. **Lambda**
   * `GetJobFn` (Python 3.12, 256 MB)  
     * GET `/v1/jobs/{id}` (API GW REST, Cognito auth)  
     * OPTIONS mock for CORS (admin + video domains)
3. **Jobs-Submit Lambda patch**
   * Persist new item `{jobId,status:"QUEUED", …}` to the table.
4. **SAM patch**
   * Extend existing `jobs-api` stack. Do **not** create a new REST API.
5. **Tests**
   * Unit tests ≥ 80 % coverage.
6. **Done when**
   * Curl `GET /v1/jobs/{id}` → 200 JSON with correct fields.
   * Front-end dashboard shows real status (frontend team will wire polling separately).

---

### 🔐 Security / IAM
Grant GetJobFn the minimal `dynamodb:GetItem` on `Jobs-${stage}` only.

---

### 📎 Context
Jobs API is at `o0fvahtccd.execute-api…`; existing Lambdas live in `frontend/backend`.  
Future work will migrate everything into a formal SAM repo, but **phase 1 is additive**. 
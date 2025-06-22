# FRONTEND-INTEGRATION AGENT – PHASE 1 SPEC
## Agent: Frontend-Integration  
## Priority: IMMEDIATE (Parallel with DevOps)

| Item         | Value                                                                                                     |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| **Repo**     | `deepfoundai/contentcraft-frontend`                                                                       |
| **Live URL** | [https://video.deepfoundai.com](https://video.deepfoundai.com)                                            |
| **Infra**    | S3 bucket `contentcraft-frontend-1750465709`, CloudFront `E12GT32WWYB30V`, Route53 zone `deepfoundai.com` |

## 0 Mission

Wire the SvelteKit frontend to the newly-deployed micro-services so that a creator can:

1. **Sign in** (JWT from Cognito → local store).
2. **Buy / see credits.**
3. **Submit a video job** ("auto" provider) and watch status update live.
4. **See finished jobs in a gallery.**

All against **dev** stage back-ends first; we'll toggle to prod when smoke tests pass.

## 1 Environment Variables

Replace the current empty placeholders with real URLs:

```bash
# .env.dev
PUBLIC_JOBS_API_URL   = https://6ydbgbao92.execute-api.us-east-1.amazonaws.com/v1    # Jobs svc
PUBLIC_CREDITS_API_URL= https://hxk5lx2y17.execute-api.us-east-1.amazonaws.com/v1    # Billing/Tiers svc
PUBLIC_AUTH_REGION    = us-east-1
PUBLIC_AUTH_USER_POOL = us-east-1_q9cVE7WTT
PUBLIC_AUTH_CLIENT_ID = 7paapnr8fbkanimk5bgpriagmg
```

**Deliverable:** 
- [ ] Committed `.env.example` updated 
- [ ] `scripts/set-env-dev.sh` that writes the correct values into SSM Parameter Store for the CI/CD workflow

## 2 API Client Layer

Use the existing typed fetch wrapper (`src/lib/api`) and add two modules:

| Module       | Methods                                                                                               |
| ------------ | ----------------------------------------------------------------------------------------------------- |
| `jobs.ts`    | `submitJob({prompt,seconds,resolution})` → returns `jobId` <br> `getJob(jobId)` <br> `listJobs(page)` |
| `credits.ts` | `getBalance()` <br> `purchasePack(tier)`                                                              |

**Implementation Steps:**
- [ ] Create `src/lib/api/jobs.ts` with job management functions
- [ ] Create `src/lib/api/credits.ts` with billing functions  
- [ ] All functions must attach `Authorization: Bearer <jwt>`
- [ ] **CRITICAL:** Use `"provider": "auto"` in `submitJob()` payload

## 3 Auth Flow

**Implementation Steps:**
- [ ] Implement **Cognito Hosted UI** redirect sign-in (no custom UI for now)
- [ ] On successful callback, store tokens in `src/lib/stores/auth.ts`
- [ ] Add simple **"Sign In / Sign Out"** button in the header
- [ ] Handle token refresh and expiration

## 4 Pages & Components

### `/dashboard` (new)
- [ ] **Credit balance** card
- [ ] **"Buy credits"** button → calls `credits.purchasePack` with Starter tier
- [ ] **Job submission** form: prompt, seconds (slider 2-10), resolution dropdown (720p only for MVP)
- [ ] **Submit** triggers `jobs.submitJob` then navigates to `/jobs/{id}`

### `/jobs/[id]`
- [ ] Poll `jobs.getJob` every 5 s until status `completed|failed`
- [ ] Show progress bar (queued / running) using existing `Spinner`
- [ ] When finished, show **MP4 video** (unsigned S3 URL provided by backend)

### `/gallery`
- [ ] Grid of last 20 completed jobs for the signed-in user

**Styling:** Stick to Tailwind utility classes already in use.

## 5 CORS & CloudFront

**Implementation Steps:**
- [ ] Extend `scripts/configure-api-cors.sh` to allow origins `https://video.deepfoundai.com` on the two API Gateways
- [ ] After build, run `aws cloudfront create-invalidation … /*`

## 6 Testing

**Implementation Steps:**
- [ ] Add Cypress e2e (`npm run e2e`) with a stub JWT to exercise:
  - sign-in redirect (mocked)
  - job submission  
  - status polling until completion (use `cy.intercept`)
- [ ] Update GitHub Action to run Cypress on every PR

## 7 Acceptance Criteria

| Item           | Metric                                                                              |
| -------------- | ----------------------------------------------------------------------------------- |
| **Build**      | `npm run build` succeeds locally & in CI                                            |
| **E2E**        | Cypress suite green                                                                 |
| **Perf**       | Initial HTML < 1 s via CloudFront (unchanged)                                       |
| **Functional** | Real video appears in gallery after submitting "Cat surfing" prompt with 8 s length |

## 8 Success Criteria & Handoff

**When done, provide:**
- [ ] PR link(s) + commit hash
- [ ] Updated `.env.example`
- [ ] Screenshot or short GIF of end-to-end flow
- [ ] Any blockers for prod cut-over

### Rollback Plan
If frontend integration causes issues:
1. Revert environment variables to previous values
2. Disable new pages (dashboard, jobs, gallery) via feature flags
3. Notify coordination team immediately
4. Investigate and fix before retry

### Integration with Routing-Manager
**Key Requirements:**
- Must use `"provider": "auto"` in job submissions
- Handle routing decisions gracefully
- Show user-friendly messages for unsupported job types
- Prepare for future ReplicateInvoker integration

---

**Focus only on the items above; infra and back-end are already handled. If anything is ambiguous, raise a `clarification:` comment in the PR rather than guessing.** 
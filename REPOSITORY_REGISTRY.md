# DeepFound AI Repository Registry

> **Last Updated:** 2025-06-21  
> **Organization:** [@deepfoundai](https://github.com/orgs/deepfoundai)  
> **Total Repositories:** 8  
> **Maintainer:** todd-deepfound

## Overview

This document serves as the central registry for all repositories under the DeepFound AI organization. It provides a structured overview of our microservices architecture and meta-agent ecosystem.

## Repository Architecture

### Service Categories

- **Core Services** (4 repos) - Main application microservices
- **Meta Agents** (4 repos) - Autonomous operational agents
- **Shared Libraries** (0 repos) - Common utilities and dependencies
- **Infrastructure** (0 repos) - IaC and deployment configurations
- **Documentation** (0 repos) - Project documentation and guides

---

## Core Services

### 🏢 cc-admin-dashboard
**Repository:** [deepfoundai/cc-admin-dashboard](https://github.com/deepfoundai/cc-admin-dashboard)

| Field | Value |
|-------|-------|
| **Category** | Core Service |
| **Type** | Full-Stack Application |
| **Tech Stack** | Python (Backend), SvelteKit (Frontend), AWS SAM |
| **Purpose** | Administrative dashboard for platform management |
| **Status** | ✅ Active |
| **Last Commit** | Initial commit: cc-admin-dashboard full-stack application |
| **Files** | 57 files, 13,461 insertions |

**Key Components:**
- Backend API with user management
- SvelteKit frontend with authentication
- AWS Cognito integration
- CloudFormation infrastructure templates

**Dependencies:**
- AWS SAM
- Python 3.9+
- Node.js 18+
- SvelteKit
- Tailwind CSS

---

### 🔐 cc-auth-svc
**Repository:** [deepfoundai/cc-auth-svc](https://github.com/deepfoundai/cc-auth-svc)

| Field | Value |
|-------|-------|
| **Category** | Core Service |
| **Type** | Microservice |
| **Tech Stack** | Python, AWS Lambda, AWS Cognito |
| **Purpose** | Authentication and user management service |
| **Status** | ✅ Active |
| **Last Commit** | Initial commit: cc-auth-svc authentication service |
| **Files** | 35 files, 2,786 insertions |

**Key Components:**
- User signup/signin handlers
- JWT token management
- Email confirmation workflow
- Session management

**API Endpoints:**
- `POST /signup` - User registration
- `POST /signin` - User authentication
- `POST /logout` - Session termination
- `POST /refresh` - Token refresh
- `POST /confirm` - Email confirmation
- `GET /me` - User profile

---

### 💳 cc-billing-tiers
**Repository:** [deepfoundai/cc-billing-tiers](https://github.com/deepfoundai/cc-billing-tiers)

| Field | Value |
|-------|-------|
| **Category** | Core Service |
| **Type** | Microservice |
| **Tech Stack** | Python, AWS Lambda, Stripe API |
| **Purpose** | Subscription billing and payment processing |
| **Status** | ✅ Active |
| **Last Commit** | Initial commit: cc-billing-tiers microservice |
| **Files** | 38 files, 5,857 insertions |

**Key Components:**
- Stripe checkout integration
- Subscription management
- Credit balance tracking
- Webhook processing
- Customer portal

**API Endpoints:**
- `POST /checkout` - Payment processing
- `GET /balance` - Credit balance
- `POST /debit` - Credit deduction
- `POST /webhook` - Stripe webhooks
- `GET /portal` - Customer portal access

---

### 🎨 cc-frontend
**Repository:** [deepfoundai/cc-frontend](https://github.com/deepfoundai/cc-frontend)

| Field | Value |
|-------|-------|
| **Category** | Core Service |
| **Type** | Frontend Application |
| **Tech Stack** | SvelteKit, TypeScript, Tailwind CSS |
| **Purpose** | Main user interface for the content creation platform |
| **Status** | ✅ Active |
| **Last Commit** | Initial commit: cc-frontend SvelteKit application |
| **Files** | 53 files, 6,567 insertions |

**Key Components:**
- SvelteKit application framework
- Responsive UI components
- API client integrations
- State management with stores
- Authentication flow

**Key Features:**
- User authentication
- Credit management dashboard
- Job submission interface
- Real-time status updates

---

## Meta Agents

### 💰 cc-agent-cost-sentinel
**Repository:** [deepfoundai/cc-agent-cost-sentinel](https://github.com/deepfoundai/cc-agent-cost-sentinel)

| Field | Value |
|-------|-------|
| **Category** | Meta Agent |
| **Type** | Monitoring Agent |
| **Tech Stack** | Python, AWS Lambda, CloudWatch |
| **Purpose** | Cost monitoring and alerting for AWS resources |
| **Status** | ✅ Active |
| **Last Commit** | Initial commit: cc-agent-cost-sentinel meta-agent |
| **Files** | 15 files, 1,627 insertions |

**Agent Capabilities:**
- AWS cost analysis
- Budget threshold monitoring
- Automated alerting
- Cost optimization recommendations

**Trigger Events:**
- Daily cost analysis
- Budget threshold breaches
- Resource utilization alerts

---

### 🔄 cc-agent-credit-reconciler
**Repository:** [deepfoundai/cc-agent-credit-reconciler](https://github.com/deepfoundai/cc-agent-credit-reconciler)

| Field | Value |
|-------|-------|
| **Category** | Meta Agent |
| **Type** | Financial Agent |
| **Tech Stack** | Python, AWS Lambda, DynamoDB |
| **Purpose** | Credit balance reconciliation and audit |
| **Status** | ✅ Active |
| **Last Commit** | Initial commit: cc-agent-credit-reconciler meta-agent |
| **Files** | 36 files, 28,050 bytes |

**Agent Capabilities:**
- Credit balance validation
- Transaction reconciliation
- Discrepancy detection
- Automated corrections

**Integrations:**
- Billing service API
- Payment processor webhooks
- User credit database

---

### 🤖 cc-agent-fal-invoker
**Repository:** [deepfoundai/cc-agent-fal-invoker](https://github.com/deepfoundai/cc-agent-fal-invoker)

| Field | Value |
|-------|-------|
| **Category** | Meta Agent |
| **Type** | AI Service Agent |
| **Tech Stack** | Python, AWS Lambda, FAL AI API |
| **Purpose** | AI model invocation and job management |
| **Status** | ✅ Active |
| **Last Commit** | Initial commit: cc-agent-fal-invoker meta-agent |
| **Files** | 19 files, 2,135 insertions |

**Agent Capabilities:**
- AI model job submission
- Queue management
- Result processing
- Error handling and retries

**AI Models Supported:**
- Image generation models
- Video generation models
- Audio processing models

---

### 📝 cc-agent-prompt-curator
**Repository:** [deepfoundai/cc-agent-prompt-curator](https://github.com/deepfoundai/cc-agent-prompt-curator)

| Field | Value |
|-------|-------|
| **Category** | Meta Agent |
| **Type** | Content Agent |
| **Tech Stack** | Python, AWS Lambda, Web Scraping |
| **Purpose** | AI prompt curation and trend analysis |
| **Status** | ✅ Active |
| **Last Commit** | Initial commit: cc-agent-prompt-curator meta-agent |
| **Files** | 14 files, 1,524 insertions |

**Agent Capabilities:**
- Trend analysis from multiple sources
- Prompt optimization suggestions
- Content quality assessment
- Market research automation

**Data Sources:**
- Social media platforms
- AI community forums
- Trending content platforms

---

## Repository Standards

### Naming Convention
- **Core Services:** `cc-{service-name}`
- **Meta Agents:** `cc-agent-{function}`
- **Shared Libraries:** `cc-lib-{library-name}`
- **Infrastructure:** `cc-infra-{component}`

### Required Files
All repositories must include:
- [ ] `README.md` - Project documentation
- [ ] `.gitignore` - Appropriate for tech stack
- [ ] `requirements.txt` or `package.json` - Dependencies
- [ ] `template.yaml` - AWS SAM template (for Lambda)
- [ ] `.github/workflows/` - CI/CD workflows (when applicable)

### Branch Strategy
- **main** - Production-ready code
- **develop** - Integration branch
- **feature/*** - Feature development
- **hotfix/*** - Emergency fixes

### Access Control
- **Organization:** Private repositories only
- **Team Access:** Based on service ownership
- **Branch Protection:** Required for main branch

---

## Maintenance Tasks

### Weekly
- [ ] Update repository status
- [ ] Review new repositories
- [ ] Check for abandoned repositories

### Monthly
- [ ] Archive inactive repositories
- [ ] Update dependency information
- [ ] Review access permissions

### Quarterly
- [ ] Full architecture review
- [ ] Documentation updates
- [ ] Performance analysis

---

## Repository Creation Checklist

When creating new repositories:

### Setup
- [ ] Create repository with appropriate name
- [ ] Set repository to private
- [ ] Add comprehensive .gitignore
- [ ] Create initial README.md
- [ ] Set up branch protection rules

### Documentation
- [ ] Update this registry file
- [ ] Add repository to organization overview
- [ ] Document dependencies and integrations
- [ ] Create deployment documentation

### Integration
- [ ] Configure CI/CD pipeline
- [ ] Set up monitoring and alerting
- [ ] Add to dependency tracking
- [ ] Update architecture diagrams

---

## Contact Information

**Repository Maintainer:** todd-deepfound  
**Organization:** [@deepfoundai](https://github.com/orgs/deepfoundai)  
**Documentation Issues:** Create issue in the appropriate repository

---

*This document is automatically updated with each repository change. Last generated: 2024-12-20* 
# Repository Template

Use this template when adding new repositories to the registry.

## Repository Entry Template

```markdown
### {EMOJI} {REPO_NAME}
**Repository:** [deepfoundai/{REPO_NAME}](https://github.com/deepfoundai/{REPO_NAME})

| Field | Value |
|-------|-------|
| **Category** | {Core Service | Meta Agent | Shared Library | Infrastructure | Documentation} |
| **Type** | {Microservice | Frontend Application | Full-Stack Application | Library | Agent | IaC} |
| **Tech Stack** | {Technologies used} |
| **Purpose** | {Brief description of purpose} |
| **Status** | {✅ Active | 🚧 In Development | ⏸️ Paused | 🗄️ Archived} |
| **Last Commit** | {Last commit message} |
| **Files** | {File count and insertions} |

**Key Components:**
- {Component 1}
- {Component 2}
- {Component 3}

{Additional sections as needed:}
**API Endpoints:** (for services)
**Agent Capabilities:** (for meta agents)
**Dependencies:** (for all)
**Key Features:** (for applications)
```

## Category Guidelines

### Core Services
- Main application microservices
- Customer-facing features
- Business logic components
- Emojis: 🏢 🔐 💳 🎨 📊 🌐 🛒 📧

### Meta Agents
- Autonomous operational agents
- Background processing
- Monitoring and automation
- Emojis: 💰 🔄 🤖 📝 🔍 ⚡ 🛡️ 📈

### Shared Libraries
- Common utilities
- Shared dependencies
- Cross-service components
- Emojis: 📚 🔧 🧩 ⚙️ 🛠️

### Infrastructure
- Infrastructure as Code
- Deployment configurations
- DevOps tooling
- Emojis: 🏗️ ☁️ 🚧 🔄 🐳 📦

### Documentation
- Project documentation
- Guides and tutorials
- Architecture documentation
- Emojis: 📖 📋 🗂️ 📝 📊

## Status Definitions

- **✅ Active** - In active development or production use
- **🚧 In Development** - Currently being developed
- **⏸️ Paused** - Development temporarily stopped
- **🗄️ Archived** - No longer maintained, kept for reference

## Quick Reference Commands

### Get repository information:
```bash
# File count and size
git ls-files | wc -l
git log --stat --oneline -1

# Last commit
git log --oneline -1

# Repository size
du -sh .git
```

### Update registry:
1. Copy template above
2. Fill in repository details
3. Add to appropriate section in REPOSITORY_REGISTRY.md
4. Update total count in header
5. Update last updated date 
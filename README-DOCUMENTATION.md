# Repository Documentation System

This documentation system provides a structured, maintainable way to track and document all repositories in the DeepFound AI organization.

## 📁 Documentation Files

### 1. [REPOSITORY_REGISTRY.md](./REPOSITORY_REGISTRY.md)
**Primary documentation file** containing comprehensive details about all repositories.

**Features:**
- Structured repository information with consistent format
- Categorized by service type (Core Services, Meta Agents, etc.)
- Rich metadata including tech stack, purpose, and status
- Direct links to GitHub repositories
- Maintenance checklists and standards

### 2. [REPOSITORY_TEMPLATE.md](./REPOSITORY_TEMPLATE.md)
**Template file** for adding new repositories to the registry.

**Features:**
- Copy-paste template for new repositories
- Category guidelines with emoji suggestions
- Status definitions and usage guidelines
- Quick reference commands for gathering repository information

### 3. [scripts/update-registry.sh](./scripts/update-registry.sh)
**Automation script** for maintaining the documentation.

**Features:**
- Scan local repositories for information
- Update registry file with current date
- Validate GitHub repositories
- Color-coded output for easy reading

## 🚀 Quick Start

### Adding a New Repository

1. **Create the repository** (locally and on GitHub)
2. **Copy the template:**
   ```bash
   # View the template
   cat REPOSITORY_TEMPLATE.md
   ```
3. **Fill in repository details** using the template format
4. **Add to registry:**
   - Open `REPOSITORY_REGISTRY.md`
   - Find the appropriate category section
   - Paste and customize the template
   - Update the total count in the header

### Updating Existing Documentation

1. **Scan repositories:**
   ```bash
   ./scripts/update-registry.sh scan
   ```

2. **Update the registry:**
   ```bash
   ./scripts/update-registry.sh update
   ```

3. **Validate GitHub repositories:**
   ```bash
   ./scripts/update-registry.sh validate
   ```

## 📊 Repository Categories

### Core Services
Main application microservices that provide business functionality:
- Authentication services
- Billing and payment processing
- Frontend applications
- Admin dashboards

### Meta Agents
Autonomous agents that handle operational tasks:
- Cost monitoring
- Credit reconciliation
- AI service orchestration
- Content curation

### Shared Libraries
Common utilities and dependencies used across services:
- Authentication libraries
- Common utilities
- Shared configurations

### Infrastructure
Infrastructure as Code and deployment configurations:
- CloudFormation templates
- Docker configurations
- CI/CD pipelines

### Documentation
Project documentation and guides:
- Architecture documentation
- API documentation
- Deployment guides

## 🎯 Benefits of This System

### For Developers
- **Quick Overview** - Easy to understand the entire system architecture
- **Consistent Information** - Standardized format for all repositories
- **Easy Navigation** - Direct links to repositories and documentation

### For Project Management
- **Status Tracking** - Clear visibility into repository status
- **Resource Planning** - Understanding of tech stacks and dependencies
- **Maintenance Scheduling** - Built-in maintenance checklists

### For New Team Members
- **Onboarding** - Comprehensive overview of all system components
- **Understanding** - Clear purpose and relationships between services
- **Quick Access** - Direct links to relevant repositories

## 📋 Maintenance Guidelines

### Daily
- Update repository status when making significant changes
- Add new repositories as they're created

### Weekly
- Run the scan script to gather current repository information
- Review and update status of repositories in development

### Monthly
- Full review of all repository information
- Update dependencies and tech stack information
- Archive inactive repositories

### Quarterly
- Comprehensive architecture review
- Update category definitions if needed
- Review and update maintenance processes

## 🔧 Script Usage

The update script provides several useful commands:

```bash
# Scan all repositories and show information
./scripts/update-registry.sh scan

# Update the registry file with current date
./scripts/update-registry.sh update

# Validate GitHub repositories exist and are accessible
./scripts/update-registry.sh validate

# Show help information
./scripts/update-registry.sh help

# Combine commands for full update
./scripts/update-registry.sh scan && ./scripts/update-registry.sh update
```

## 🎨 Customization

### Adding New Categories
1. Update the category list in `REPOSITORY_REGISTRY.md`
2. Add emoji guidelines in `REPOSITORY_TEMPLATE.md`
3. Update the script to scan new category directories

### Changing Information Fields
1. Update the template in `REPOSITORY_TEMPLATE.md`
2. Update existing entries in `REPOSITORY_REGISTRY.md`
3. Update the script to gather new information types

### Repository Naming Conventions
Current conventions:
- Core Services: `cc-{service-name}`
- Meta Agents: `cc-agent-{function}`
- Shared Libraries: `cc-lib-{library-name}`
- Infrastructure: `cc-infra-{component}`

## 📞 Support

For questions or improvements to this documentation system:
1. Create an issue in the relevant repository
2. Contact the repository maintainer: todd-deepfound
3. Submit a pull request with improvements

---

*This documentation system is designed to scale with your organization as you add more repositories and team members.* 
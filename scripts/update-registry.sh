#!/bin/bash

# Repository Registry Update Script
# This script helps gather information about repositories for the registry

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY_FILE="$SCRIPT_DIR/../REPOSITORY_REGISTRY.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get repository information
get_repo_info() {
    local repo_dir="$1"
    local repo_name=$(basename "$repo_dir")
    
    if [[ ! -d "$repo_dir/.git" ]]; then
        print_warning "Not a git repository: $repo_dir"
        return 1
    fi
    
    cd "$repo_dir"
    
    # Get repository information
    local file_count=$(git ls-files | wc -l | tr -d ' ')
    local last_commit=$(git log --oneline -1 2>/dev/null || echo "No commits")
    local branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    local remote_url=$(git remote get-url origin 2>/dev/null || echo "No remote")
    
    # Get lines of code (rough estimate)
    local total_lines=$(git ls-files | xargs wc -l 2>/dev/null | tail -n 1 | awk '{print $1}' || echo "0")
    
    echo "Repository: $repo_name"
    echo "  Files: $file_count"
    echo "  Total lines: $total_lines"
    echo "  Last commit: $last_commit"
    echo "  Branch: $branch"
    echo "  Remote: $remote_url"
    echo ""
}

# Function to scan all repositories
scan_repositories() {
    print_status "Scanning repositories..."
    
    # Core services
    local core_services=(
        "admin/cc-admin-dashboard"
        "auth/cc-auth-svc"
        "frontend"
        "cc-billing-tiers"
    )
    
    # Meta agents
    local meta_agents=(
        "meta-agents/cc-agent-cost-sentinel"
        "meta-agents/cc-agent-credit-reconciler"
        "meta-agents/cc-agent-fal-invoker"
        "meta-agents/cc-agent-prompt-curator"
    )
    
    echo "=== CORE SERVICES ==="
    for service in "${core_services[@]}"; do
        if [[ -d "$service" ]]; then
            get_repo_info "$service"
        else
            print_warning "Directory not found: $service"
        fi
    done
    
    echo "=== META AGENTS ==="
    for agent in "${meta_agents[@]}"; do
        if [[ -d "$agent" ]]; then
            get_repo_info "$agent"
        else
            print_warning "Directory not found: $agent"
        fi
    done
}

# Function to update registry file
update_registry() {
    print_status "Updating registry file..."
    
    # Update the last updated date
    local current_date=$(date +"%Y-%m-%d")
    sed -i.bak "s/Last Updated: [0-9-]*/Last Updated: $current_date/" "$REGISTRY_FILE"
    
    print_status "Registry updated with current date: $current_date"
}

# Function to validate GitHub repositories
validate_github_repos() {
    print_status "Validating GitHub repositories..."
    
    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed. Please install it to validate repositories."
        return 1
    fi
    
    # List repositories
    gh repo list deepfoundai --limit 50 --json name,url,isPrivate,updatedAt | jq -r '
        .[] | "\(.name) - \(.url) - Private: \(.isPrivate) - Updated: \(.updatedAt)"
    ' 2>/dev/null || {
        print_error "Failed to fetch repository list from GitHub"
        return 1
    }
}

# Function to show help
show_help() {
    cat << EOF
Repository Registry Update Script

Usage: $0 [OPTIONS]

OPTIONS:
    scan        Scan local repositories and show information
    update      Update the registry file with current date
    validate    Validate GitHub repositories
    help        Show this help message

Examples:
    $0 scan                 # Scan all local repositories
    $0 update               # Update registry file
    $0 validate             # Check GitHub repositories
    $0 scan && $0 update    # Scan and update registry
EOF
}

# Main script logic
main() {
    case "${1:-scan}" in
        "scan")
            scan_repositories
            ;;
        "update")
            update_registry
            ;;
        "validate")
            validate_github_repos
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 
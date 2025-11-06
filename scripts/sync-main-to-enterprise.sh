#!/bin/bash
# Enhanced sync script: main → Enterprise (with safety checks)
# Usage: ./scripts/sync-main-to-enterprise.sh "Your commit message"

set -e  # Exit on any error

MAIN_BRANCH="main"
ENTERPRISE_BRANCH="Enterprise-Grade-DMS-Module-Records-Management"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Sync Main → Enterprise Branch${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Get commit message from argument or use default
COMMIT_MSG="${1:-sync: Sync main changes to Enterprise branch}"

# Check if we're on the main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "$MAIN_BRANCH" ]; then
    echo -e "${YELLOW}⚠️  Currently on: $CURRENT_BRANCH${NC}"
    echo -e "${BLUE}Switching to: $MAIN_BRANCH${NC}"
    git checkout "$MAIN_BRANCH"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ You have uncommitted changes on main!${NC}"
    echo -e "${YELLOW}Please commit or stash them first:${NC}"
    git status --short
    exit 1
fi

echo -e "${GREEN}✅ Main branch is clean${NC}"

# Check if Enterprise branch exists
if ! git show-ref --verify --quiet refs/heads/"$ENTERPRISE_BRANCH"; then
    echo -e "${YELLOW}⚠️  Enterprise branch doesn't exist. Creating from main...${NC}"
    git checkout -b "$ENTERPRISE_BRANCH"
    git checkout "$MAIN_BRANCH"
fi

# Show what will be synced
echo -e "\n${BLUE}📊 Changes to sync:${NC}"
git log "$ENTERPRISE_BRANCH..$MAIN_BRANCH" --oneline --max-count=5

# Check if there are actually changes to sync
if git diff --quiet "$ENTERPRISE_BRANCH..$MAIN_BRANCH"; then
    echo -e "${GREEN}✅ Branches are already in sync${NC}"
    exit 0
fi

# Confirm before proceeding
echo -e "\n${YELLOW}This will:${NC}"
echo -e "  1. Switch to ${ENTERPRISE_BRANCH}"
echo -e "  2. Merge ${MAIN_BRANCH} → ${ENTERPRISE_BRANCH}"
echo -e "  3. Push to origin/${ENTERPRISE_BRANCH}"
echo -e "  4. Return to ${MAIN_BRANCH}"
echo -e "\n${YELLOW}Continue? (y/N):${NC} "
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Cancelled.${NC}"
    exit 0
fi

# Switch to Enterprise branch
echo -e "\n${BLUE}Switching to $ENTERPRISE_BRANCH...${NC}"
git checkout "$ENTERPRISE_BRANCH"

# Pull latest to avoid conflicts
echo -e "${BLUE}Pulling latest $ENTERPRISE_BRANCH...${NC}"
git pull origin "$ENTERPRISE_BRANCH" || true  # Don't fail if no remote

# Merge main into Enterprise
echo -e "${BLUE}Merging $MAIN_BRANCH → $ENTERPRISE_BRANCH...${NC}"
if git merge "$MAIN_BRANCH" --no-ff -m "$COMMIT_MSG"; then
    echo -e "${GREEN}✅ Merge successful${NC}"
else
    echo -e "${RED}❌ Merge failed - please resolve conflicts manually${NC}"
    exit 1
fi

# Push to remote
echo -e "${BLUE}Pushing to origin/$ENTERPRISE_BRANCH...${NC}"
if git push origin "$ENTERPRISE_BRANCH"; then
    echo -e "${GREEN}✅ Pushed to remote${NC}"
else
    echo -e "${YELLOW}⚠️  Could not push to remote${NC}"
fi

# Return to main branch
echo -e "${BLUE}Returning to $MAIN_BRANCH...${NC}"
git checkout "$MAIN_BRANCH"

echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ SUCCESS! Enterprise branch synchronized${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📍 Current branch:${NC} $(git rev-parse --abbrev-ref HEAD)"
echo -e "${BLUE}🔄 Enterprise branch:${NC} $(git rev-parse --short "$ENTERPRISE_BRANCH")"
echo ""

# Show final status
echo -e "${BLUE}📊 Final sync status:${NC}"
git log --oneline --graph -n 3 --decorate "$MAIN_BRANCH" "$ENTERPRISE_BRANCH"

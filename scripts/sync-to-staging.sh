#!/bin/bash
# Safe sync script: Enterprise → main (staging/development on Odoo.sh)
# Usage: ./scripts/sync-to-staging.sh "Your commit message"

set -e  # Exit on any error

ENTERPRISE_BRANCH="Enterprise-Grade-DMS-Module-Records-Management"
STAGING_BRANCH="main"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deploy to Staging: Enterprise → main (Odoo.sh Dev)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Get commit message from argument or use default
COMMIT_MSG="${1:-sync: Deploy tested changes from Enterprise to staging (main)}"

# Check if we're on the Enterprise branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$ENTERPRISE_BRANCH" ]; then
    echo -e "${YELLOW}⚠️  Currently on: $CURRENT_BRANCH${NC}"
    echo -e "${BLUE}Switching to: $ENTERPRISE_BRANCH${NC}"
    git checkout "$ENTERPRISE_BRANCH"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ You have uncommitted changes!${NC}"
    echo -e "${YELLOW}Please commit or stash them first:${NC}"
    git status --short
    exit 1
fi

echo -e "${GREEN}✅ Enterprise branch is clean${NC}"

# Show what will be synced
echo -e "\n${BLUE}📊 Changes to sync:${NC}"
git log "$STAGING_BRANCH..$ENTERPRISE_BRANCH" --oneline --max-count=5

# Confirm before proceeding
echo -e "\n${YELLOW}This will:${NC}"
echo -e "  1. Switch to ${STAGING_BRANCH}"
echo -e "  2. Merge ${ENTERPRISE_BRANCH} → ${STAGING_BRANCH}"
echo -e "  3. Push to origin/${STAGING_BRANCH} (triggers Odoo.sh staging deployment)"
echo -e "  4. Return to ${ENTERPRISE_BRANCH}"
echo -e "\n${YELLOW}Continue? (y/N):${NC} "
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Cancelled.${NC}"
    exit 0
fi

# Switch to staging branch
echo -e "\n${BLUE}Switching to $STAGING_BRANCH...${NC}"
git checkout "$STAGING_BRANCH"

# Pull latest to avoid conflicts
echo -e "${BLUE}Pulling latest $STAGING_BRANCH...${NC}"
git pull origin "$STAGING_BRANCH"

# Merge Enterprise into Staging
echo -e "${BLUE}Merging $ENTERPRISE_BRANCH → $STAGING_BRANCH...${NC}"
git merge "$ENTERPRISE_BRANCH" --no-ff -m "$COMMIT_MSG"

# Push to trigger deployment
echo -e "${BLUE}Pushing to origin/$STAGING_BRANCH (deploying to Odoo.sh staging)...${NC}"
git push origin "$STAGING_BRANCH"

# Return to Enterprise branch
echo -e "${BLUE}Returning to $ENTERPRISE_BRANCH...${NC}"
git checkout "$ENTERPRISE_BRANCH"

echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ SUCCESS! Staging deployment triggered on Odoo.sh${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📍 Current branch:${NC} $(git branch --show-current)"
echo -e "${BLUE}🚀 Odoo.sh staging is deploying from:${NC} $STAGING_BRANCH"
echo -e "${BLUE}💡 Monitor deployment at:${NC} https://odoo.sh"
echo ""

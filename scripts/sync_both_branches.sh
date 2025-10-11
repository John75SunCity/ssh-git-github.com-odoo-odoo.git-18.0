#!/bin/bash

# Sync Both Branches Script - Always update main and Enterprise branches simultaneously
# Usage: ./sync_both_branches.sh "commit message"

set -e  # Exit on any error

COMMIT_MSG="${1:-'fix: Automated dual-branch synchronization'}"
MAIN_BRANCH="main"
ENTERPRISE_BRANCH="Enterprise-Grade-DMS-Module-Records-Management"

echo "🔄 Starting dual-branch synchronization..."

# Ensure we're on main branch
echo "📋 Ensuring we're on main branch..."
git checkout "$MAIN_BRANCH"

# Add all changes and commit on main
echo "📦 Committing changes to main branch..."
git add .
if git diff --staged --quiet; then
    echo "✅ No changes to commit on main branch"
else
    git commit -m "$COMMIT_MSG"
    echo "✅ Changes committed to main branch"
fi

# Push main branch
echo "⬆️ Pushing main branch..."
git push origin "$MAIN_BRANCH"

# Switch to Enterprise branch and merge
echo "🔄 Switching to Enterprise branch..."
git checkout "$ENTERPRISE_BRANCH"

echo "🔀 Merging main into Enterprise branch..."
git merge "$MAIN_BRANCH"

# Push Enterprise branch
echo "⬆️ Pushing Enterprise branch..."
git push origin "$ENTERPRISE_BRANCH"

# Return to main branch
echo "🔙 Returning to main branch..."
git checkout "$MAIN_BRANCH"

# Final verification
echo "✅ Dual-branch synchronization complete!"
echo "📊 Final status:"
echo "Main branch: $(git rev-parse --short HEAD)"
git checkout "$ENTERPRISE_BRANCH"
echo "Enterprise branch: $(git rev-parse --short HEAD)"
git checkout "$MAIN_BRANCH"

echo ""
echo "🎯 Both branches are now synchronized and pushed to origin!"

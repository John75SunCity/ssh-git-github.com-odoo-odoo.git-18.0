#!/bin/bash
# Auto Sync Main Branch Script
# Automatically keeps main branch updated with working branch changes

echo "🔄 Starting Auto Main Branch Sync..."

# Get current branch name
WORKING_BRANCH=$(git branch --show-current)
MAIN_BRANCH="main"

echo "📋 Working Branch: $WORKING_BRANCH"
echo "🎯 Target Branch: $MAIN_BRANCH"

# Function to sync main branch
sync_main_branch() {
    while true; do
        echo "⏰ Checking for sync opportunity: $(date)"
        
        # Check if we're in a git repo
        if [ ! -d ".git" ]; then
            echo "❌ Not in a git repository"
            sleep 300
            continue
        fi
        
        # Check if we have commits ahead of origin
        AHEAD_COUNT=$(git rev-list --count origin/${WORKING_BRANCH}..HEAD 2>/dev/null || echo "0")
        
        if [ "$AHEAD_COUNT" -gt "0" ]; then
            echo "📤 Found $AHEAD_COUNT commits ahead of origin. Syncing main branch..."
            
            # Fetch latest changes
            git fetch origin 2>/dev/null || echo "⚠️  Fetch failed"
            
            # Switch to main branch
            if git checkout $MAIN_BRANCH 2>/dev/null; then
                echo "✅ Switched to $MAIN_BRANCH branch"
                
                # Merge working branch into main
                if git merge origin/${WORKING_BRANCH} --no-ff -m "AUTO SYNC: Merge ${WORKING_BRANCH} into ${MAIN_BRANCH} ($(date))" 2>/dev/null; then
                    echo "🔀 Successfully merged $WORKING_BRANCH into $MAIN_BRANCH"
                    
                    # Push main branch
                    if git push origin $MAIN_BRANCH 2>/dev/null; then
                        echo "📤 Successfully pushed $MAIN_BRANCH to GitHub"
                    else
                        echo "⚠️  Failed to push $MAIN_BRANCH - will retry later"
                    fi
                else
                    echo "⚠️  Merge failed - manual intervention may be required"
                fi
                
                # Switch back to working branch
                git checkout $WORKING_BRANCH 2>/dev/null || echo "⚠️  Failed to switch back to $WORKING_BRANCH"
                
            else
                echo "⚠️  Failed to switch to $MAIN_BRANCH branch"
            fi
        else
            echo "✅ Main branch is up to date"
        fi
        
        # Wait 10 minutes before next check
        sleep 600
    done
}

# Run in background
sync_main_branch &
SYNC_PID=$!

echo "✅ Auto sync started (PID: $SYNC_PID)"
echo "📝 To stop: kill $SYNC_PID"
echo "🔄 Sync checking every 10 minutes..."
echo "📋 Manual workflow preserved - this only syncs main branch automatically"

# Save PID for easy killing later
echo $SYNC_PID > /tmp/auto_sync_main.pid

echo "📖 How it works:"
echo "   1. You manually commit and push to $WORKING_BRANCH"
echo "   2. This script detects new commits and automatically merges them to $MAIN_BRANCH"
echo "   3. $MAIN_BRANCH stays synchronized without affecting your workflow"
echo ""
echo "🎯 Your workflow remains unchanged - commit and push manually as desired!"

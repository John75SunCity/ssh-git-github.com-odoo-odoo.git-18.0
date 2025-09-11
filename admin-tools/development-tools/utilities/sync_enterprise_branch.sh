#!/bin/bash
# Auto Sync Enterprise Branch Script
# Automatically keeps Enterprise-Grade-DMS-Module-Records-Management branch updated with main branch changes

echo "🔄 Starting Auto Enterprise Branch Sync..."

MAIN_BRANCH="main"
ENTERPRISE_BRANCH="Enterprise-Grade-DMS-Module-Records-Management"

echo "📋 Main Branch: $MAIN_BRANCH"
echo "🎯 Enterprise Branch: $ENTERPRISE_BRANCH"

# Function to sync enterprise branch
sync_enterprise_branch() {
    while true; do
        echo "⏰ Checking for sync opportunity: $(date)"
        
        # Check if we're in a git repo
        if [ ! -d ".git" ]; then
            echo "❌ Not in a git repository"
            sleep 300
            continue
        fi
        
        # Fetch latest changes
        git fetch origin 2>/dev/null || echo "⚠️  Fetch failed"
        
        # Check if main has new commits not in enterprise branch
        MAIN_AHEAD=$(git rev-list --count origin/${ENTERPRISE_BRANCH}..origin/${MAIN_BRANCH} 2>/dev/null || echo "0")
        
        if [ "$MAIN_AHEAD" -gt "0" ]; then
            echo "📤 Main branch has $MAIN_AHEAD new commits. Syncing Enterprise branch..."
            
            # Get current branch for restoration
            CURRENT_BRANCH=$(git branch --show-current)
            
            # Switch to enterprise branch
            if git checkout $ENTERPRISE_BRANCH 2>/dev/null; then
                echo "✅ Switched to $ENTERPRISE_BRANCH branch"
                
                # Pull latest enterprise changes first
                git pull origin $ENTERPRISE_BRANCH 2>/dev/null || echo "⚠️  Pull failed"
                
                # Merge main into enterprise branch
                if git merge origin/${MAIN_BRANCH} --no-ff -m "AUTO SYNC: Merge ${MAIN_BRANCH} into ${ENTERPRISE_BRANCH} ($(date))" 2>/dev/null; then
                    echo "🔀 Successfully merged $MAIN_BRANCH into $ENTERPRISE_BRANCH"
                    
                    # Push enterprise branch
                    if git push origin $ENTERPRISE_BRANCH 2>/dev/null; then
                        echo "📤 Successfully pushed $ENTERPRISE_BRANCH to GitHub"
                    else
                        echo "⚠️  Failed to push $ENTERPRISE_BRANCH - will retry later"
                    fi
                else
                    echo "⚠️  Merge failed - manual intervention may be required"
                fi
                
                # Switch back to original branch (should be main)
                if [ "$CURRENT_BRANCH" != "$ENTERPRISE_BRANCH" ]; then
                    git checkout $CURRENT_BRANCH 2>/dev/null || echo "⚠️  Failed to switch back to $CURRENT_BRANCH"
                fi
            else
                echo "❌ Failed to switch to $ENTERPRISE_BRANCH branch"
            fi
        else
            echo "✅ Enterprise branch is up to date with main"
        fi
        
        # Wait 10 minutes before checking again
        echo "💤 Waiting 10 minutes before next check..."
        sleep 600
    done
}

# Check if we want to run in background
if [ "$1" = "start" ]; then
    echo "🚀 Starting Enterprise branch sync in background..."
    sync_enterprise_branch &
    SYNC_PID=$!
    echo "✅ Enterprise sync started (PID: $SYNC_PID)"
    echo "📝 To stop: kill $SYNC_PID"
    echo "🔄 Sync running every 10 minutes..."
    
    # Save PID for easy killing later
    echo $SYNC_PID > /tmp/enterprise_sync.pid
    echo "💾 PID saved to /tmp/enterprise_sync.pid"
elif [ "$1" = "stop" ]; then
    if [ -f "/tmp/enterprise_sync.pid" ]; then
        SYNC_PID=$(cat /tmp/enterprise_sync.pid)
        kill $SYNC_PID 2>/dev/null && echo "✅ Stopped enterprise sync (PID: $SYNC_PID)" || echo "⚠️  Process not found or already stopped"
        rm -f /tmp/enterprise_sync.pid
    else
        echo "❌ No PID file found. Process may not be running."
    fi
elif [ "$1" = "once" ]; then
    echo "🔄 Running one-time sync..."
    # Fetch latest changes
    git fetch origin 2>/dev/null || echo "⚠️  Fetch failed"
    
    # Check if main has new commits
    MAIN_AHEAD=$(git rev-list --count origin/${ENTERPRISE_BRANCH}..origin/${MAIN_BRANCH} 2>/dev/null || echo "0")
    
    if [ "$MAIN_AHEAD" -gt "0" ]; then
        echo "📤 Main branch has $MAIN_AHEAD new commits. Syncing..."
        
        # Switch to enterprise branch
        git checkout $ENTERPRISE_BRANCH
        git pull origin $ENTERPRISE_BRANCH
        git merge origin/${MAIN_BRANCH} --no-ff -m "MANUAL SYNC: Merge ${MAIN_BRANCH} into ${ENTERPRISE_BRANCH} ($(date))"
        git push origin $ENTERPRISE_BRANCH
        git checkout $MAIN_BRANCH
        
        echo "✅ One-time sync completed"
    else
        echo "✅ Enterprise branch is already up to date"
    fi
else
    echo "📖 Usage:"
    echo "  $0 start   - Start background sync service"
    echo "  $0 stop    - Stop background sync service"
    echo "  $0 once    - Run one-time sync now"
    echo ""
    echo "💡 This script keeps Enterprise-Grade-DMS-Module-Records-Management branch"
    echo "   updated with changes from main branch automatically."
fi

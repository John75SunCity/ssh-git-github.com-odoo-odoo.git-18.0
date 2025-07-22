#!/bin/bash
# VS Code Session Maintenance Script
# Run this in background to keep your session alive

echo "🚀 Starting VS Code session maintenance..."

# Function to keep session alive
keep_alive() {
    while true; do
        # Send a keepalive every 5 minutes
        echo "⏰ Keepalive: $(date)"
        
        # Touch a temp file to show activity
        touch /tmp/vscode_keepalive_$(date +%s)
        
        # Clean old keepalive files (keep only last 10)
        ls -t /tmp/vscode_keepalive_* 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
        
        # Auto-save current work (if git repo)
        if [ -d ".git" ]; then
            git add . 2>/dev/null || true
            git commit -m "AUTO: Session keepalive save $(date)" 2>/dev/null || true
        fi
        
        # Wait 5 minutes
        sleep 300
    done
}

# Run in background
keep_alive &
KEEPALIVE_PID=$!

echo "✅ Session maintenance started (PID: $KEEPALIVE_PID)"
echo "📝 To stop: kill $KEEPALIVE_PID"
echo "🔄 Keepalive running every 5 minutes..."

# Save PID for easy killing later
echo $KEEPALIVE_PID > /tmp/vscode_keepalive.pid

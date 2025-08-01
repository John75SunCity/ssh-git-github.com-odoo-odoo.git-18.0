#!/bin/bash
echo "🛑 Stopping session keep-alive..."
pkill -f "keep_session_active_5hr.sh" 2>/dev/null || true
rm -f /tmp/session_heartbeat_* 2>/dev/null || true
echo "✅ Session keep-alive stopped"

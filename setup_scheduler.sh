#!/bin/bash
# ==============================================================================
# setup_scheduler.sh — Automated Daily Job Hunt Scheduler for macOS
# ==============================================================================
# This script sets up a background macOS launchd service that automatically
# executes the Job Search Automation pipeline daily at 09:00 AM (local time).
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PLIST_NAME="com.venuskondapalli.jobhunt"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
LOG_OUT="$DIR/logs/scheduler_out.log"
LOG_ERR="$DIR/logs/scheduler_err.log"

mkdir -p "$DIR/logs"
mkdir -p "$HOME/Library/LaunchAgents"

show_help() {
    echo "Usage: ./setup_scheduler.sh [install | uninstall | status | run-now]"
    echo ""
    echo "Commands:"
    echo "  install    - Schedule daily automatic run at 9:00 AM via launchd"
    echo "  uninstall  - Remove the scheduled task"
    echo "  status     - Check scheduler status"
    echo "  run-now    - Trigger immediate background execution"
    echo ""
}

case "$1" in
    install|"")
        echo "==> Creating macOS LaunchAgent at: $PLIST_PATH"
        cat << EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${DIR}/run_job_search.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${DIR}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>10</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${LOG_OUT}</string>
    <key>StandardErrorPath</key>
    <string>${LOG_ERR}</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

        # Unload if already loaded, then load
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        launchctl load "$PLIST_PATH"

        echo "✅ Scheduler installed and loaded successfully!"
        echo "   Schedule: Daily at 10:00 AM"
        echo "   Script:   $DIR/run_job_search.sh"
        echo "   Logs:     $DIR/logs/"
        ;;

    uninstall)
        echo "==> Unloading and removing LaunchAgent..."
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        rm -f "$PLIST_PATH"
        echo "✅ Scheduled task removed."
        ;;

    status)
        echo "==> Checking LaunchAgent status..."
        if launchctl list | grep -q "$PLIST_NAME"; then
            echo "✅ $PLIST_NAME is ACTIVE in launchctl"
            launchctl list | grep "$PLIST_NAME"
        else
            echo "ℹ️  $PLIST_NAME is not currently loaded."
        fi
        if [ -f "$PLIST_PATH" ]; then
            echo "📄 Plist file exists at: $PLIST_PATH"
        else
            echo "⚠️  Plist file not found at: $PLIST_PATH"
        fi
        ;;

    run-now)
        echo "==> Triggering immediate run via launchctl..."
        launchctl start "$PLIST_NAME"
        echo "✅ Job started. Check logs: $LOG_OUT"
        ;;

    *)
        show_help
        ;;
esac

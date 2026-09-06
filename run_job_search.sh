#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "============================================================"
echo "  UI/UX Job Search Automation System (macOS)"
echo "  Running at $(date)"
echo "============================================================"

"$DIR/.venv/bin/python" main.py "$@"

echo ""
echo "============================================================"
echo "  Done! Open jobs_dashboard.html to view results."
echo "  Path: file://$DIR/jobs_dashboard.html"
echo "============================================================"

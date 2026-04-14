#!/bin/bash
# Refresh Feishu media URLs from Bitable and optionally push to GitHub.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$HOME/.logs/refresh-videos.log"

mkdir -p "$(dirname "$LOG_FILE")"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Feishu Bitable refresh..." | tee -a "$LOG_FILE"
python3 "$REPO_DIR/refresh.py" 2>&1 | tee -a "$LOG_FILE"

# Git commit and push
cd "$REPO_DIR"
git add api/videos.json api/covers.json api/portfolio.json
git diff --cached --quiet && echo "[$(date '+%Y-%m-%d %H:%M:%S')] No changes to commit." | tee -a "$LOG_FILE" && exit 0

git commit -m "chore: refresh Feishu media URLs [$(date '+%Y-%m-%d %H:%M')]"
git push origin main
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pushed to GitHub." | tee -a "$LOG_FILE"

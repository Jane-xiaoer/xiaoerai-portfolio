#!/bin/bash
# Refresh Feishu video URLs and push to GitHub
# Run every ~20h via launchd to keep URLs fresh before they expire at 24h

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_FILE="$REPO_DIR/api/videos.json"
LOG_FILE="$HOME/.logs/refresh-videos.log"

mkdir -p "$(dirname "$LOG_FILE")"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting video URL refresh..." | tee -a "$LOG_FILE"

# All 46 video tokens from Feishu Bitable
TOKENS='["Al0Xbi5PioKbckxy6NscTgR0n2g","YXcZbP4LgomNinxtm6KcccapnVc","HjembEj07oSwa9xMUtncND1anDi","FTQTbyKSKot76Pxb56GcmRlJnzf","JWIbbCJRaoU4pfxdRIycnjOfnve","PnHDbmIrhogyzlxYt6WcJTz9nVd","NCP9bVUaxoufMXxGeWlcJI7XnSe","DhdgbiP8lofMpqxOwRrcOOlFnQf","BMXLbLqH1obvRTxsycicd20Sneh","LCw3bLV73opArEx74eocbexon9b","Xg6mbcSxpoDjAlxsadkcOC9rn8b","SXUzbn5QSorwYSxYFa5cOqNrn4b","WDSEbIhK2owK8hxwMcCc9ITenmb","ESTyb8ZDooXq20xhr7Bc31lanff","Kc5Ybw24boj0ywxxf6ycIW7CnMb","FwC2bmTfxoziBzxgm1AcGsAVnFh","VfI9bCdAcoK5owxEp04chcacn3e","PBOMbcO21o3LuCxVBfuctuSsnje","XYXybsYSUouWH5xO8Yxc6lwTnIj","IGa4br37boMyS2xBFmmc24WvnVb","GQVibPzRfoPs0VxIee2cE7AZnch","DRWAb5TsVoIt1vxIvvScUe0SnDd","Ge3gbJYPnoMODMxKN5lct2Gbn1g","CtAbbt87QoojmwxP4CPc80A8nzd","HnlGb4yTloTSIPx1vNuc95BknQe","RFIUb7NPgovTj7xBtsWcfOUTnfd","LIWMbxmoGou4p1xbObQc4nSrn1g","NnsUbFwGioSLHLxzRp3c0n7mnxb","AEV2bWIIxoEJaxxqEUocAlNinBh","LyU5bDlecoX5vzx7sThc7k3Oncf","FopYbCSvAoguvQxUzx7cRhBTneh","RqUibvkSHoC1ZZxTODVcu80jnKm","LAZ5b2QBOoSm6XxsesHcepCJn7e","TmrmbEa2ZoqSY4xzPXccAZt7n5f","HG1jblXQPolaxExQdwXclJjwnJe","PNWob5owSo0K50xfschcVrKPnsu","CFewbtjoboOQ4DxReoxcTiLYnmd","U0v4bGhGzoZkbXxfEwYceGqrnsb","LJBob0vVVoVlFtxk0iDcNprhnZf","Wh4ZbUqTPo9uwqxq0nycLvTdnIe","BFpPbzmB7omxsXxcjTBcG9wqnCg","IWIzbezWJo9W6Ix2B5McV64znch","FbjIbwnk0osonPxYNhOc5eQWnFf","KyK9bTN1zoBtPexCZJOcx6tlnqh","FArZbJbd8ow2EjxNq2jcbY8anrg","OvoMbO0UaoPxJfxlBKLcWFspnHf"]'

# Call Feishu API via lark-cli
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Calling Feishu API..." | tee -a "$LOG_FILE"
RESULT=$(lark-cli api GET /open-apis/drive/v1/medias/batch_get_tmp_download_url --params "{\"file_tokens\":$TOKENS}" 2>&1)

# Check success
CODE=$(echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('code', -1))" 2>/dev/null || echo "-1")
if [ "$CODE" != "0" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: API call failed. Code=$CODE" | tee -a "$LOG_FILE"
  echo "$RESULT" >> "$LOG_FILE"
  exit 1
fi

# Build token→url map and write to api/videos.json
echo "$RESULT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
urls = d['data']['tmp_download_urls']
result = {item['file_token']: item['tmp_download_url'] for item in urls}
result['_refreshed_at'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
print(json.dumps(result, indent=2))
" > "$OUTPUT_FILE"

URL_COUNT=$(python3 -c "import json; d=json.load(open('$OUTPUT_FILE')); print(len([k for k in d if not k.startswith('_')]))")
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Got $URL_COUNT fresh URLs → $OUTPUT_FILE" | tee -a "$LOG_FILE"

# Git commit and push
cd "$REPO_DIR"
git add api/videos.json
git diff --cached --quiet && echo "[$(date '+%Y-%m-%d %H:%M:%S')] No changes to commit." | tee -a "$LOG_FILE" && exit 0

git commit -m "chore: refresh Feishu video URLs [$(date '+%Y-%m-%d %H:%M')]"
git push origin main
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pushed to GitHub." | tee -a "$LOG_FILE"

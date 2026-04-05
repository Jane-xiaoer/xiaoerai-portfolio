#!/usr/bin/env python3
"""
Refresh Feishu video URLs and write to api/videos.json.
Calls lark-cli in batches of 5 (API limit per call).
"""

import json
import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
OUTPUT_FILE = REPO_DIR / "api" / "videos.json"
LOG_FILE = Path.home() / ".logs" / "refresh-videos.log"

# All 46 video tokens from Feishu Bitable
ALL_TOKENS = [
    "Al0Xbi5PioKbckxy6NscTgR0n2g", "YXcZbP4LgomNinxtm6KcccapnVc",
    "HjembEj07oSwa9xMUtncND1anDi", "FTQTbyKSKot76Pxb56GcmRlJnzf",
    "JWIbbCJRaoU4pfxdRIycnjOfnve", "PnHDbmIrhogyzlxYt6WcJTz9nVd",
    "NCP9bVUaxoufMXxGeWlcJI7XnSe", "DhdgbiP8lofMpqxOwRrcOOlFnQf",
    "BMXLbLqH1obvRTxsycicd20Sneh", "LCw3bLV73opArEx74eocbexon9b",
    "Xg6mbcSxpoDjAlxsadkcOC9rn8b", "SXUzbn5QSorwYSxYFa5cOqNrn4b",
    "WDSEbIhK2owK8hxwMcCc9ITenmb", "ESTyb8ZDooXq20xhr7Bc31lanff",
    "Kc5Ybw24boj0ywxxf6ycIW7CnMb", "FwC2bmTfxoziBzxgm1AcGsAVnFh",
    "VfI9bCdAcoK5owxEp04chcacn3e", "PBOMbcO21o3LuCxVBfuctuSsnje",
    "XYXybsYSUouWH5xO8Yxc6lwTnIj", "IGa4br37boMyS2xBFmmc24WvnVb",
    "GQVibPzRfoPs0VxIee2cE7AZnch", "DRWAb5TsVoIt1vxIvvScUe0SnDd",
    "Ge3gbJYPnoMODMxKN5lct2Gbn1g", "CtAbbt87QoojmwxP4CPc80A8nzd",
    "HnlGb4yTloTSIPx1vNuc95BknQe", "RFIUb7NPgovTj7xBtsWcfOUTnfd",
    "LIWMbxmoGou4p1xbObQc4nSrn1g", "NnsUbFwGioSLHLxzRp3c0n7mnxb",
    "AEV2bWIIxoEJaxxqEUocAlNinBh", "LyU5bDlecoX5vzx7sThc7k3Oncf",
    "FopYbCSvAoguvQxUzx7cRhBTneh", "RqUibvkSHoC1ZZxTODVcu80jnKm",
    "LAZ5b2QBOoSm6XxsesHcepCJn7e", "TmrmbEa2ZoqSY4xzPXccAZt7n5f",
    "HG1jblXQPolaxExQdwXclJjwnJe", "PNWob5owSo0K50xfschcVrKPnsu",
    "CFewbtjoboOQ4DxReoxcTiLYnmd", "U0v4bGhGzoZkbXxfEwYceGqrnsb",
    "LJBob0vVVoVlFtxk0iDcNprhnZf", "Wh4ZbUqTPo9uwqxq0nycLvTdnIe",
    "BFpPbzmB7omxsXxcjTBcG9wqnCg", "IWIzbezWJo9W6Ix2B5McV64znch",
    "FbjIbwnk0osonPxYNhOc5eQWnFf", "KyK9bTN1zoBtPexCZJOcx6tlnqh",
    "FArZbJbd8ow2EjxNq2jcbY8anrg", "OvoMbO0UaoPxJfxlBKLcWFspnHf",
]

BATCH_SIZE = 5


def log(msg):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def fetch_batch(tokens):
    params = json.dumps({"file_tokens": tokens})
    result = subprocess.run(
        ["lark-cli", "api", "GET",
         "/open-apis/drive/v1/medias/batch_get_tmp_download_url",
         "--params", params],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"lark-cli failed: {result.stderr.strip() or 'no output'}")
    data = json.loads(result.stdout)
    if data.get("code") != 0:
        raise RuntimeError(f"API error code={data.get('code')}: {data.get('msg')}")
    return {item["file_token"]: item["tmp_download_url"]
            for item in data["data"]["tmp_download_urls"]}


def main():
    log(f"Starting refresh for {len(ALL_TOKENS)} tokens in batches of {BATCH_SIZE}...")

    url_map = {}
    batches = [ALL_TOKENS[i:i+BATCH_SIZE] for i in range(0, len(ALL_TOKENS), BATCH_SIZE)]

    for i, batch in enumerate(batches, 1):
        try:
            urls = fetch_batch(batch)
            url_map.update(urls)
            log(f"Batch {i}/{len(batches)}: got {len(urls)} URLs")
        except Exception as e:
            log(f"ERROR batch {i}: {e}")
            sys.exit(1)

    url_map["_refreshed_at"] = datetime.now(timezone.utc).isoformat()
    url_map["_count"] = len(ALL_TOKENS)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(url_map, indent=2))
    log(f"Written {len(ALL_TOKENS)} URLs to {OUTPUT_FILE}")

    # Git commit and push
    os.chdir(REPO_DIR)
    status = subprocess.run(["git", "diff", "--cached", "--quiet", "--", "api/videos.json"],
                            capture_output=True)
    subprocess.run(["git", "add", "api/videos.json"], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if diff.returncode == 0:
        log("No changes to commit.")
        return

    ts_short = datetime.now().strftime("%Y-%m-%d %H:%M")
    subprocess.run(["git", "commit", "-m", f"chore: refresh Feishu video URLs [{ts_short}]"],
                   check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    log("Pushed to GitHub.")


if __name__ == "__main__":
    main()

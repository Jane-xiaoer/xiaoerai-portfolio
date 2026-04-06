#!/usr/bin/env python3
"""
Refresh Feishu video + cover URLs and write to api/videos.json and api/covers.json.
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
COVERS_FILE = REPO_DIR / "api" / "covers.json"
LOG_FILE = Path.home() / ".logs" / "refresh-videos.log"

# All 44 video tokens from Feishu Bitable (ordered by 序号)
ALL_TOKENS = [
    "Al0Xbi5PioKbckxy6NscTgR0n2g", "PnHDbmIrhogyzlxYt6WcJTz9nVd",
    "WDSEbIhK2owK8hxwMcCc9ITenmb", "U0v4bGhGzoZkbXxfEwYceGqrnsb",
    "YXcZbP4LgomNinxtm6KcccapnVc", "JWIbbCJRaoU4pfxdRIycnjOfnve",
    "NCP9bVUaxoufMXxGeWlcJI7XnSe", "IGa4br37boMyS2xBFmmc24WvnVb",
    "FopYbCSvAoguvQxUzx7cRhBTneh", "DhdgbiP8lofMpqxOwRrcOOlFnQf",
    "GQVibPzRfoPs0VxIee2cE7AZnch", "LAZ5b2QBOoSm6XxsesHcepCJn7e",
    "LCw3bLV73opArEx74eocbexon9b", "Ge3gbJYPnoMODMxKN5lct2Gbn1g",
    "VfI9bCdAcoK5owxEp04chcacn3e", "Xg6mbcSxpoDjAlxsadkcOC9rn8b",
    "HjembEj07oSwa9xMUtncND1anDi", "HnlGb4yTloTSIPx1vNuc95BknQe",
    "XYXybsYSUouWH5xO8Yxc6lwTnIj", "DRWAb5TsVoIt1vxIvvScUe0SnDd",
    "CtAbbt87QoojmwxP4CPc80A8nzd", "HG1jblXQPolaxExQdwXclJjwnJe",
    "LIWMbxmoGou4p1xbObQc4nSrn1g", "FTQTbyKSKot76Pxb56GcmRlJnzf",
    "NnsUbFwGioSLHLxzRp3c0n7mnxb", "AEV2bWIIxoEJaxxqEUocAlNinBh",
    "LyU5bDlecoX5vzx7sThc7k3Oncf", "PBOMbcO21o3LuCxVBfuctuSsnje",
    "RqUibvkSHoC1ZZxTODVcu80jnKm", "LJBob0vVVoVlFtxk0iDcNprhnZf",
    "TmrmbEa2ZoqSY4xzPXccAZt7n5f", "Wh4ZbUqTPo9uwqxq0nycLvTdnIe",
    "IWIzbezWJo9W6Ix2B5McV64znch", "PNWob5owSo0K50xfschcVrKPnsu",
    "SXUzbn5QSorwYSxYFa5cOqNrn4b", "KyK9bTN1zoBtPexCZJOcx6tlnqh",
    "CFewbtjoboOQ4DxReoxcTiLYnmd", "BFpPbzmB7omxsXxcjTBcG9wqnCg",
    "FbjIbwnk0osonPxYNhOc5eQWnFf", "OvoMbO0UaoPxJfxlBKLcWFspnHf",
    "Kc5Ybw24boj0ywxxf6ycIW7CnMb", "T1ivbgZ29o0mn0xr3KRceSwHn5f",
    "ESTyb8ZDooXq20xhr7Bc31lanff", "RFIUb7NPgovTj7xBtsWcfOUTnfd",
]

# All 44 cover image tokens from Feishu Bitable (ordered by 序号)
ALL_COVER_TOKENS = [
    "XIi5bHICko2l20xpad3cNUQ3nqg", "BDKxbH9WVoXHRpxKB6WcqestnOb",
    "IaDrbeps2o0VcIxgnaXcoUBYnfb", "QBqkb2IZOopj51x1cVyc2RONntf",
    "DDd5bh64XoBEHoxuOjCcj7xInuh", "EKFUbk03aoVllsxqtqRcqUApn6e",
    "X7Yrb6I55oqBI7x7sAocL7oIncg", "LmFvbWzrWoSDuNxThqVcS6Gonke",
    "SW3IbyWc8oo15Bxx5K4cDSR6nWe", "WU7ObY9laowtG4xxBH5c3o1znOg",
    "AZuZb8PQ3oYmgHxCSsNcgw0tn4e", "K9tDbmGQ6oE08txlCi3c1cmIn8f",
    "GVn3byufPox0i6xcAfbcGd6cnHf", "QfsJbaVHlo14OIx1kSYcaQaZnOg",
    "F0gtbyAFgo0w6gxflvVc19Wpn7c", "BDRubrdnDoOWRsxYCVfcSQQtnnf",
    "XH6RbxYNNoobSFx4a1UcWQsznHd", "K4gIbjRnloUB61x23AMcPd5dnmi",
    "SBmMbEBOdoQB7OxRQ41cDtEDnue", "CwkkbR3kto8Kf5xpm2ucOMRQntb",
    "PshUbMbNroDsUVxWRlycgFOmnhe", "EwN8blijho8239xDGdrcPqBQnlg",
    "AORYbfqr4ohUWLxY31bcBv7DnJe", "KxpwbdxzWobMf6xQEOtcNdwDnbo",
    "TztBbWwPiotgqGxdHzmc6RInnte", "EoDfbJ08do26NJxFSJwcFmWonQg",
    "T6U5bDNl2o06FIxZdEbc20iBnbf", "BASdb68ZuoaTFvxrlhGcqeLunfe",
    "JWIjbJiMCopzh1x7vkxcFj8Yn2b", "UhpCb9jBgohZy1xs2CjcuwWwneb",
    "DwhDbrHnDorPQfxWJlNct8s3nJh", "IG3SbpxaRofKRpxrONmcTqZen4g",
    "IetKblvxyoxu4ZxYHjncu8udnBs", "H9L4b3ibXo5VoQxiZ25chOKHnRg",
    "VwjcbOjX8oeJ8UxaGZqccPHtnOc", "YV03bApAfoueaLxY7HIcVjHGnYe",
    "Okpjbqg4UorUIHxl1oYcNlBMnrb", "WdnmbAs8goWVQZxdqMgcFc54nuh",
    "XogCb3Z5coiJfRxmFKicteksnnb", "U5MbbD5YRorXkNxLKJoc0V6Unyg",
    "MvIYb4iGVoHLdqxZgdfcfR1VnwT", "ZjaKbBLnjo2MmfxxwIFcW1NwnBh",
    "JmlMbL4Gfo3Cy7xYwTbczcP5nmg", "HA6NbtpwtooewSx5Xurc4fvEnPf",
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
         "--params", params, "--as", "bot"],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"lark-cli failed: {result.stderr.strip() or 'no output'}")
    data = json.loads(result.stdout)
    if data.get("code") != 0:
        raise RuntimeError(f"API error code={data.get('code')}: {data.get('msg')}")
    return {item["file_token"]: item["tmp_download_url"]
            for item in data["data"]["tmp_download_urls"]}


def refresh_all(token_list, label):
    url_map = {}
    batches = [token_list[i:i+BATCH_SIZE] for i in range(0, len(token_list), BATCH_SIZE)]
    for i, batch in enumerate(batches, 1):
        try:
            urls = fetch_batch(batch)
            url_map.update(urls)
            log(f"[{label}] Batch {i}/{len(batches)}: got {len(urls)} URLs")
        except Exception as e:
            log(f"[{label}] ERROR batch {i}: {e}")
            sys.exit(1)
    return url_map


def main():
    log(f"Starting refresh: 44 videos + {len(ALL_COVER_TOKENS)} covers")

    # Refresh video URLs
    url_map = refresh_all(ALL_TOKENS, "video")
    url_map["_refreshed_at"] = datetime.now(timezone.utc).isoformat()
    url_map["_count"] = len(ALL_TOKENS)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(url_map, indent=2))
    log(f"Written {len(ALL_TOKENS)} video URLs to {OUTPUT_FILE}")

    # Refresh cover URLs
    cover_map = refresh_all(ALL_COVER_TOKENS, "cover")
    COVERS_FILE.write_text(json.dumps(cover_map, indent=2))
    log(f"Written {len(ALL_COVER_TOKENS)} cover URLs to {COVERS_FILE}")

    # Git commit and push
    os.chdir(REPO_DIR)
    subprocess.run(["git", "add", "api/videos.json", "api/covers.json"], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if diff.returncode == 0:
        log("No changes to commit.")
        return

    ts_short = datetime.now().strftime("%Y-%m-%d %H:%M")
    subprocess.run(["git", "commit", "-m", f"chore: refresh Feishu URLs [{ts_short}]"],
                   check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    log("Pushed to GitHub.")


if __name__ == "__main__":
    main()

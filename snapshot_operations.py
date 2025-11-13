import os
import time
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()


def poll_snapshot_status(
    snapshot_id: str, max_attempts: int = 60, delay: int = 5
) -> bool:
    print("snapshot id inside poll snapshot status:", snapshot_id)
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    progress_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(max_attempts):
        try:
            print(
                f"⏳ Checking snapshot progress... (attempt {attempt + 1}/{max_attempts})"
            )

            response = requests.get(progress_url, headers=headers)
            response.raise_for_status()

            progress_data = response.json()
            status = progress_data.get("status")

            if status == "ready":
                print("✅ Snapshot completed!")
                return True
            elif status == "failed":
                print("❌ Snapshot failed")
                return False
            elif status == "running":
                print("🔄 Still processing...")
                time.sleep(delay)
            else:
                print(f"❓ Unknown status: {status}")
                time.sleep(delay)

        except Exception as e:
            print(f"⚠️ Error checking progress: {e}")
            time.sleep(delay)

    print("⏰ Timeout waiting for snapshot completion")
    return False


def download_snapshot(
    snapshot_id: str, format: str = "json"
) -> Optional[List[Dict[Any, Any]]]:
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    download_url = (
        f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format={format}"
    )
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        print("📥 Downloading snapshot data...")

        response = requests.get(download_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        print(
            f"🎉 Successfully downloaded {len(data) if isinstance(data, list) else 1} items"
        )

        return data

    except Exception as e:
        print(f"❌ Error downloading snapshot: {e}")
        return None

# import os
# import time
# import json
# import requests
# from typing import List, Dict, Any, Iterable, Optional

# # ---------- Helpers ----------

# def _ensure_list_of_dicts(obj: Any) -> List[Dict[str, Any]]:
#     """Return list[dict]; filter out non-dict rows safely."""
#     if obj is None:
#         return []
#     if isinstance(obj, dict):
#         # Some Bright Data JSON wraps rows in "items"/"data"
#         for key in ("items", "data", "results", "documents"):
#             val = obj.get(key)
#             if isinstance(val, list):
#                 return [x for x in val if isinstance(x, dict)]
#         return [obj]
#     if isinstance(obj, (list, tuple)):
#         return [x for x in obj if isinstance(x, dict)]
#     return []

# def _parse_ndjson_lines(lines: Iterable[str]) -> List[Dict[str, Any]]:
#     items: List[Dict[str, Any]] = []
#     for line in lines:
#         if not line:
#             continue
#         s = line.strip()
#         if not s:
#             continue
#         try:
#             row = json.loads(s)
#             if isinstance(row, dict):
#                 items.append(row)
#         except Exception:
#             # skip non-JSON (e.g., progress/messages)
#             continue
#     return items

# # ---------- Robust Polling ----------

# def poll_snapshot_status(
#     snapshot_id: str,
#     deadline_seconds: int = 180,    # overall wall-clock timeout
#     base_delay: float = 2.0,        # backoff start
#     max_delay: float = 8.0,         # backoff cap
# ) -> bool:
#     api_key = os.getenv("BRIGHTDATA_API_KEY")
#     progress_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
#     headers = {"Authorization": f"Bearer {api_key}"}

#     start = time.time()
#     delay = base_delay

#     while True:
#         elapsed = time.time() - start
#         if elapsed > deadline_seconds:
#             print("⏰ Timeout waiting for snapshot completion")
#             return False

#         try:
#             print(f"⏳ Checking snapshot progress... (t+{int(elapsed)}s)")
#             r = requests.get(progress_url, headers=headers, timeout=30)
#             r.raise_for_status()
#             jd = r.json()

#             status = (jd.get("status") or "").lower()
#             if status in {"ready", "completed", "done"}:
#                 print("✅ Snapshot completed!")
#                 return True
#             if status in {"failed", "aborted", "timeout", "timed_out"}:
#                 print(f"❌ Snapshot failed with status: {status}")
#                 return False

#             print(f"🔄 Still processing... status={status!r} progress={jd.get('progress')}")
#             time.sleep(delay)
#             delay = min(max_delay, delay * 1.5)

#         except Exception as e:
#             print(f"⚠️ Error checking progress: {e}")
#             time.sleep(delay)
#             delay = min(max_delay, delay * 1.5)

# # ---------- Robust Download (JSON → JSONL fallback) ----------

# def download_snapshot(snapshot_id: str) -> List[Dict[str, Any]]:
#     """
#     Tries JSON first, then falls back to JSONL (NDJSON).
#     ALWAYS returns list[dict] (empty list on failure).
#     """
#     api_key = os.getenv("BRIGHTDATA_API_KEY")
#     headers = {"Authorization": f"Bearer {api_key}"}

#     # 1) Try JSON
#     try:
#         url_json = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
#         print("📥 Downloading snapshot data (JSON)...")
#         r = requests.get(url_json, headers=headers, timeout=120)
#         r.raise_for_status()

#         # some servers send json with text/plain; try json() regardless
#         data = r.json()
#         items = _ensure_list_of_dicts(data)
#         print(f"🎉 JSON download: {len(items)} items")
#         if items:
#             return items
#     except Exception as e:
#         print(f"ℹ️ JSON download failed or empty, will try JSONL: {e}")

#     # 2) Fallback: JSONL / NDJSON
#     try:
#         url_jsonl = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=jsonl"
#         print("📥 Downloading snapshot data (JSONL)...")
#         r = requests.get(url_jsonl, headers=headers, stream=True, timeout=120)
#         r.raise_for_status()

#         # iterate lines to avoid loading entire file
#         lines = (
#             line.decode("utf-8", "ignore")
#             if isinstance(line, (bytes, bytearray)) else line
#             for line in r.iter_lines(decode_unicode=True)
#         )
#         items = _parse_ndjson_lines(lines)
#         print(f"🎉 JSONL download: {len(items)} items")
#         return items
#     except Exception as e:
#         print(f"❌ Error downloading snapshot: {e}")
#         return []


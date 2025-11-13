import json
import time
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, quote_plus
import requests
import os

BRIGHTDATA_API_URL = "https://api.brightdata.com/request"
BRIGHTDATA_ZONE = "ai_agent"  # <-- keep your zone name here
REQUESTS_PER_SECOND = 1.0      # throttle to be nice to the API
GOOGLE_BASE = "https://www.google.com/search"

# Keep only safe/essential params; drop tracking like utm_*, fbclid, etc.
_DROP_QUERY_PREFIXES = ("utm_", "gclid", "yclid", "fbclid", "spm", "igshid")
_KEEP_QUERY_EXACT = set(["v", "t", "si", "feature"])  # keep YT video id, etc.

def _clean_url(u: str) -> str:
    try:
        p = urlparse(u)
        # Normalize hostname (e.g., m.facebook.com -> facebook.com when possible)
        netloc = p.netloc.lower()
        netloc = netloc.replace("m.facebook.com", "www.facebook.com").replace("mobile.twitter.com", "twitter.com")
        netloc = netloc.replace("x.com", "twitter.com")  # unify x.com/twitter.com

        # Remove tracking params
        q = []
        for k, v in parse_qsl(p.query, keep_blank_values=True):
            if k in _KEEP_QUERY_EXACT or not k.startswith(_DROP_QUERY_PREFIXES):
                if not any(k.startswith(pref) for pref in _DROP_QUERY_PREFIXES) or k in _KEEP_QUERY_EXACT:
                    q.append((k, v))
        query = urlencode(q)

        # Strip fragments
        cleaned = urlunparse((p.scheme, netloc, p.path.rstrip("/"), "", query, ""))

        # Remove trailing slash duplicates (but keep root slash)
        if cleaned.endswith("/") and cleaned.count("/") > 2:
            cleaned = cleaned.rstrip("/")

        return cleaned
    except Exception:
        return u

def _uniq_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def _extract_urls_from_serp_json(full_response):
    """
    Tries to pull URLs from common Bright Data + brd_json=1 structures.
    Returns a flat list of url strings.
    """
    urls = []

    if not full_response:
        return urls

    # Case 1: Bright Data already parsed fields
    for key in ("organic", "results", "inline_results"):
        if isinstance(full_response.get(key), list):
            for item in full_response[key]:
                for lk in ("link", "url"):
                    if isinstance(item, dict) and lk in item and isinstance(item[lk], str):
                        urls.append(item[lk])

    # Case 2: Sometimes payload is nested
    data = full_response.get("data") or full_response.get("content") or None
    if isinstance(data, dict):
        for key in ("organic", "results", "inline_results"):
            if isinstance(data.get(key), list):
                for item in data[key]:
                    for lk in ("link", "url"):
                        if isinstance(item, dict) and lk in item and isinstance(item[lk], str):
                            urls.append(item[lk])

    # Fallback: if Bright Data returned a JSON string
    if isinstance(full_response, str):
        try:
            obj = json.loads(full_response)
            urls.extend(_extract_urls_from_serp_json(obj))
        except Exception:
            pass

    # Clean + dedupe
    urls = [_clean_url(u) for u in urls if isinstance(u, str) and u.startswith("http")]
    return _uniq_keep_order(urls)

def _google_serp(query: str, num: int = 50, start: int = 0, hl: str = "en") -> list:
    """
    Runs a single Google query via Bright Data and returns extracted URLs.
    """
    # Note: brd_json=1 asks Bright Data to return a structured JSON for the page
    target_url = f"{GOOGLE_BASE}?q={quote_plus(query)}&num={num}&start={start}&hl={hl}&brd_json=1"

    payload = {
        "zone": BRIGHTDATA_ZONE,
        "url": target_url,
        "format": "raw"  # Bright Data will return the parsed JSON fields (organic, etc.) when brd_json=1 is set
    }

    full_response = _make_api_request(BRIGHTDATA_API_URL, json=payload)
    return _extract_urls_from_serp_json(full_response)

def serp_search_platform(query: str, platform_query: str, max_urls: int = 1) -> list:
    """
    Searches Google for `query` constrained by `platform_query` (e.g., site filters),
    returns up to max_urls URLs.
    """
    # Try first page; optionally, you could paginate with start=10,20 if needed.
    urls = _google_serp(f"{query} {platform_query}", num=50, start=0)
    urls = [u for u in urls if u]  # non-empty
    return urls[:max_urls]

def collect_platform_urls(user_question: str, max_per_platform: int = 1, throttle: float = REQUESTS_PER_SECOND) -> dict:
    """
    For each platform, builds a smart site/inurl filter query and returns up to 10 URLs.
    """
    # Tailored filters to bias toward posts/reels/videos where applicable
    PLATFORM_QUERIES = {
        "Reddit":    '(site:reddit.com OR site:old.reddit.com) (inurl:/r/ OR inurl:/comments/)',
        "Youtube":   '(site:youtube.com OR site:youtu.be) (inurl:/watch OR inurl:/shorts OR inurl:youtu.be/)',
        "Tiktok":    '(site:tiktok.com) (inurl:/video/ OR inurl:/@)',
        "Instagram": '(site:instagram.com) (inurl:/p/ OR inurl:/reel/)',
        "Facebook":  '(site:facebook.com OR site:m.facebook.com) (inurl:/posts/ OR inurl:/reel/)',
        "X":         '((site:x.com OR site:twitter.com)) (inurl:/status/ OR inurl:/i/web/status/)',
        "LinkedIn":  '(site:linkedin.com) (inurl:/posts/)',
    }

    results = {}
    last_time = 0.0

    for platform, plat_query in PLATFORM_QUERIES.items():
        # simple throttle
        elapsed = time.time() - last_time
        min_interval = 1.0 / max(throttle, 0.001)
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        combined = f'({user_question}) {plat_query}'
        urls = serp_search_platform(combined, "", max_urls=max_per_platform)  # platform query already combined
        results[platform] = urls
        last_time = time.time()

    return results

def print_urls_only(results: dict):
    """
    Prints ONLY URLs (no headings) in a deterministic order (platform order, then link order).
    """
    platform_order = ["Reddit", "Youtube", "Tiktok", "Instagram", "Facebook", "X", "LinkedIn"]
    for p in platform_order:
        for u in results.get(p, []):
            print(u)

# ---------------------------
# Replace this with your real HTTP caller:
def _make_api_request(url, **kwargs):
    api_key = os.getenv("BRIGHTDATA_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except Exception as e:
        print(f"Unknown error: {e}")
        return None
# ---------------------------

# if __name__ == "__main__":
#     user_question = "is elon musk is a good person"  # <-- replace with your dynamic input
#     results = collect_platform_urls(user_question, max_per_platform=10)
#     final_output = json.dumps(results, indent=4, ensure_ascii=False)
#     print(final_output)

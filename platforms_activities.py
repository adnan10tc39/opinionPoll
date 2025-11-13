from collections import defaultdict

def summarize_platform_activity(platform_post_urls: dict, comments_data: dict) -> str:
    """
    Build a summary like:
      Platform
      Posts=#
      Comments=#
    for every platform found in either input.

    Rules:
    - Posts = count of URLs in platform_post_urls[platform].
    - If a platform has 0 URLs but comments_data[platform] looks like a list of search/results dicts
      (e.g., Google/Bing with 'title'/'description'), treat len(list) as Posts.
    - Comments = number of non-empty comment items. Handles:
        * dicts with 'comment_text' as str
        * dicts with 'comment_text' as list[str]
        * ignores None/empty strings
    - Case-insensitive platform merging; canonical name is Title Case of the first-seen key.
    """

    # --- helpers ---
    def canon(name: str) -> str:
        # Title-case but keep common stylings
        fixed = {
            "x": "X",
            "youtube": "Youtube",
            "tiktok": "Tiktok",
            "linkedin": "LinkedIn",
            "facebook": "Facebook",
            "instagram": "Instagram",
            "google": "Google",
            "bing": "Bing",
            "reddit": "Reddit",
        }
        return fixed.get(name.lower(), name.title())

    def count_comments(items) -> int:
        """Count meaningful comments in a heterogenous list of dicts."""
        if not isinstance(items, list):
            return 0
        total = 0
        for entry in items:
            if not isinstance(entry, dict):
                continue
            if "comment_text" in entry:
                ct = entry["comment_text"]
                if isinstance(ct, str):
                    if ct and str(ct).strip().lower() != "none":
                        total += 1
                elif isinstance(ct, list):
                    total += sum(
                        1 for s in ct
                        if isinstance(s, str) and s.strip() and s.strip().lower() != "none"
                    )
                # else: ignore non-string/list comment_text
        return total

    def looks_like_search_results(items) -> bool:
        """Heuristic for Google/Bing-style search result lists."""
        if not isinstance(items, list) or not items:
            return False
        # treat as results if most items are dicts with 'title' or 'description'
        hits = 0
        checked = 0
        for entry in items[:5]:  # small sample
            checked += 1
            if isinstance(entry, dict) and ("title" in entry or "description" in entry):
                hits += 1
        return checked > 0 and hits >= max(1, checked // 2)

    # --- merge keys case-insensitively, remember a canonical label for display ---
    all_keys = {}
    def remember(name):
        key = name.lower()
        if key not in all_keys:
            all_keys[key] = canon(name)
        return key

    posts_by = defaultdict(int)
    comments_by = defaultdict(int)

    # Posts from URL dict
    if isinstance(platform_post_urls, dict):
        for k, urls in platform_post_urls.items():
            lk = remember(k)
            posts_by[lk] += len(urls) if isinstance(urls, list) else 0

    # Comments (and possible "search-result posts") from comments dict
    if isinstance(comments_data, dict):
        for k, items in comments_data.items():
            lk = remember(k)
            comments_by[lk] += count_comments(items)
            # If no URL posts exist for this platform, but list looks like search results,
            # treat those as "Posts"
            if posts_by[lk] == 0 and looks_like_search_results(items):
                posts_by[lk] = len(items)

    # Build ordered output (alphabetical by display name)
    lines = []
    for lk, display in sorted(all_keys.items(), key=lambda kv: kv[1].lower()):
        lines.append(display)
        lines.append(f"Posts={posts_by[lk]}")
        if comments_by[lk] > 0:
            lines.append(f"Comments={comments_by[lk]}")
    return "\n".join(lines)

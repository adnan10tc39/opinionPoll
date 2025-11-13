from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from snapshot_operations import download_snapshot, poll_snapshot_status
from openai import OpenAI
import json
from platforms_activities import summarize_platform_activity
import time 

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


# def _make_api_request(url, **kwargs):
#     api_key = os.getenv("BRIGHTDATA_API_KEY")
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json",
#     }
#     print("prepared_urls nnamNA", url)
#     try:
#         response = requests.post(url, headers=headers, **kwargs)
#         response.raise_for_status()
        
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"API request failed: {e}")
#         return None
#     except Exception as e:
#         print(f"Unknown error: {e}")
#         return None


def _make_api_request(url, **kwargs):
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    attempt = 0  # kitni dafa try ho chuka hai

    while True:  # jab tak success na ho jaye
        attempt += 1
        print(f"[TRY {attempt}] prepared_urls nnamNA {url}")

        try:
            response = requests.post(url, headers=headers, **kwargs)
            response.raise_for_status()  # 4xx / 5xx pe exception throw karega

            # yahan pohanch gaye matlab success ho gaya
            print(f"[SUCCESS] Status: {response.status_code}")
            return response.json()

        except requests.exceptions.RequestException as e:
            # network error, timeout, 5xx, etc.
            wait_seconds = min(60, 2 ** attempt)  # 2, 4, 8, 16... max 60 sec
            print(f"[ERROR] API request failed: {e}")
            print(f"[INFO] {wait_seconds} seconds baad dobara try kar raha hoon...")
            time.sleep(wait_seconds)

        except Exception as e:
            # koi unexpected error
            wait_seconds = min(60, 2 ** attempt)
            print(f"[UNKNOWN ERROR] {e}")
            print(f"[INFO] {wait_seconds} seconds baad dobara try kar raha hoon...")
            time.sleep(wait_seconds)



def _trigger_and_download_snapshot(trigger_url, params, data, operation_name="operation"):
    trigger_result = _make_api_request(trigger_url, params=params, json=data)
    if not trigger_result:
        return None
    
    snapshot_id = trigger_result.get("snapshot_id")
    print(snapshot_id)
    if not snapshot_id:
        return None

    if not poll_snapshot_status(snapshot_id):
        return None
    raw_data = download_snapshot(snapshot_id)
    return raw_data





def serp_search(query, engine="google"):
    if engine == "google":
        base_url = "https://www.google.com/search"
    elif engine == "bing":
        base_url = "https://www.bing.com/search"
    else:
        raise ValueError(f"Unknown engine {engine}")

    url = "https://api.brightdata.com/request"

    payload = {
        "zone": "ai_agent",
        "url": f"{base_url}?q={quote_plus(query)}&brd_json=1",
        "format": "raw"
    }

    full_response = _make_api_request(url, json=payload)
    if not full_response:
        return None

    organic_results = full_response.get("organic", [])
    extracted_data = [{"title": item.get("title"), "description": item.get("description")} for item in organic_results]
    # extracted_data = {
    #     "knowledge": full_response.get("knowledge", {}),
    #     "organic": full_response.get("organic", []),
    # }
    return extracted_data

def reddit_comment_retrieval(urls, days_back=10, load_all_replies=False, comment_limit=5):
    if not urls:
        return None

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
    params = {
        "dataset_id": "gd_lvzdpsdlw09j6t702",
        "include_errors": "true"
    }

    data = [
        {
            "url": url,
            "days_back": days_back,
            "load_all_replies": load_all_replies,
            "comment_limit": comment_limit
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="reddit comments"
    )
    if not raw_data:
        return None

    parsed_comments = []
    for comment in raw_data:
        parsed_comment = {
            "comment_text": comment.get("comment"),
        }
        parsed_comments.append(parsed_comment)

    return parsed_comments


#******************** YouTube*************************
def youtube_post_retrieval(urls, num_of_comments=5, sort_by="Newest first"):
    if not urls:
        return None

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
  
    params = {
        "dataset_id": "gd_lk9q0ew71spt1mxywf",
        "include_errors": "true"
    }

    data = [
        {
            "url": url,
            "num_of_comments":num_of_comments,
            "sort_by": sort_by
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="youtube comments"
    )
    if not raw_data:
        return None

    parsed_comments = []
    for comment in raw_data:
        parsed_comment = {
            "comment_text": comment.get("comment_text")
        }
        parsed_comments.append(parsed_comment)

    return parsed_comments

#******************** YouTube end*************************

#******************** Tiktok  *************************

def tiktok_post_retrieval(urls):
    if not urls:
        return None

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
  
    params = {
        "dataset_id": "gd_lkf2st302ap89utw5k",
        "include_errors": "true"
    }

    data = [
        {
            "url": url,
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="tiktok comments"
    )
    if not raw_data:
        return None

    parsed_comments = []
    for comment in raw_data:
        parsed_comment = {
            "comment_text": comment.get("comment_text")
        }
        parsed_comments.append(parsed_comment)

    return parsed_comments

#******************** Tiktok End*************************


#******************** Instagram  *************************

def instagram_comments_retrieval(urls):
    if not urls:
        return None

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
  
    params = {
        "dataset_id": "gd_ltppn085pokosxh13",
        "include_errors": "true"
    }

    data = [
        {
            "url": url,
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="instagram comments"
    )
    if not raw_data:
        return None

    parsed_comments = []
    for comment in raw_data:
        parsed_comment = {
            "comment_text": comment.get("comment")
        }
        parsed_comments.append(parsed_comment)

    return parsed_comments

#******************** Instagram End*************************


#******************** Facebook  *************************

def facebook_comments_retrieval(urls,get_all_replies=False,limit_records=5, comments_sort="Most relevant"):
    if not urls:
        return None

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
  
    params = {
        "dataset_id": "gd_lkay758p1eanlolqw8",
        "include_errors": "true"

    }

    data = [
        {
            "url": url,
            "get_all_replies":get_all_replies,
            "limit_records":limit_records, 
            "comments_sort": comments_sort
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="facebook comments"
    )
    if not raw_data:
        return None

    parsed_comments = []
    for comment in raw_data:
        parsed_comment = {
            "comment_text": comment.get("comment_text")
        }
        parsed_comments.append(parsed_comment)

    return parsed_comments

#******************** Facebook End*************************

#********************  X  *************************

def x_comments_retrieval(urls):
    if not urls:
        return None

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
  
    params = {
        "dataset_id": "gd_lwxkxvnf1cynvib9co",
        "include_errors": "true"
    }

    data = [
        {
            "url": url,
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="x comments"
    )
    if not raw_data:
        return None

    parsed_comments = []
    for comment in raw_data:
        parsed_comment = {
            "comment_text": comment.get("description")
        }
        parsed_comments.append(parsed_comment)

    return parsed_comments

#******************** X End  *************************


#********************  LinkedIn  *************************

def linkedin_comments_retrieval(urls):
    if not urls:
        return None

    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
  
    params = {
        "dataset_id": "gd_lyy3tktm25m4avu764",
        "include_errors": "true"
    }

    data = [
        {
            "url": url,
        }
        for url in urls
    ]

    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="linkedin comments"
    )
    if not raw_data:
        return None

    parsed_comments = []
    for comment in raw_data:
        top_comments = comment.get("top_visible_comments") or []
        extracted_comments = [c.get("comment") for c in top_comments if isinstance(c, dict)]
        parsed_comment = {
            "post_text": comment.get("post_text"),
            "comment_text":extracted_comments
        }
        parsed_comments.append(parsed_comment)

    return parsed_comments

#******************** LinkedIn End  *************************

# def results_curation(comments_json, user_query):
#     # social_urls is ignored intentionally; we only use comments_json + user_query

#     system_prompt = """
#         You are an expert social listening and opinion-poll analyst.

#         Your job:
#         - Analyze social media comments as an informal opinion poll about the user question.
#         - Use ONLY the provided comments_json (platform-wise comments).
#         - Treat results as a convenience sample (not representative of a whole population).
#         - Focus on: clear options, counts, approximate percentages, and a short, decision-ready interpretation.

#         Style:
#         - Be concise, direct, and suitable for politics / business questions.
#         - Use simple language and short paragraphs.
#         - No speculation beyond the provided comments.
#         - If you estimate numbers, clearly mark them with words like "about", "around", "roughly".
#     """.strip()

#     report_prompt = f"""
#         USER QUESTION
#         {user_query}

#         INPUT DATA — COMMENTS JSON (platform-wise comments)
#         {json.dumps(comments_json, indent=2, ensure_ascii=False)}

#         YOUR TASK

#         - Treat the USER QUESTION as the main poll question.
#         - First, infer 2–5 clear opinion OPTIONS that answer this question.
#           Examples of option patterns (for guidance only):
#             - Support / Oppose / Neutral
#             - Candidate A / Candidate B / Candidate C / Neutral
#             - Optimistic / Pessimistic / Neutral
#             - Yes / No / Neutral
#         - Build the options from the meaning of the USER QUESTION and the patterns in the comments, not from the user directly.
#         - Then classify the comments into those options as if each comment is one "vote".
#         - If many comments have no clear stance, use an option like "Neutral / Unclear".

#         RULES ABOUT NUMBERS
#         - If comments_json already contains explicit counts, percentages, or labels per option, use them exactly.
#         - If only raw comments are provided, infer approximate counts/percentages based on visible patterns.
#             - Use small integers and whole-number percentages.
#             - Make it clear that counts/percentages are approximate (e.g., "about 30 comments (≈40%)").
#         - Never claim the results represent a whole country, market, or population.
#           Always frame them as being based only on the analyzed social media comments.

#         DELIVERABLE FORMAT

#         Write a short, decision-ready report with the following sections and headings:

#         1) Opinion Poll Setup
#         - 2–3 sentences:
#             - Restate the USER QUESTION in your own words.
#             - Mention that you analyzed social media comments as an informal opinion poll.
#             - Briefly state the OPTIONS you will use.
#         - Then list the options as bullet points, each with a very short explanation.

#         2) Opinion Poll Results — Counts and Percentages
#         - Present a simple text summary, one line per option, like:
#             - Option: X — about N comments (≈P%)
#         - Include only options supported by the comments.
#         - If you use a Neutral/Unclear or Other option, include it.
#         - Ensure percentages roughly sum to 100%.
#         - After the lines, add a short paragraph (2–4 sentences) that:
#             - Clearly states which option is leading (if any).
#             - Mentions if the race is close or one-sided.

#         3) Key Insights
#         - 2–4 bullet points that interpret what the results mean for a politics/business decision-maker.
#         - Focus on:
#             - What the dominant option suggests (e.g., support vs resistance, preference for one candidate/product).
#             - The main reasons or themes visible in the comments (only based on comments_json).
#             - Any important minority view worth noting.

#         4) Limitations
#         - 1–2 sentences explaining that:
#             - This is an informal social media opinion snapshot.
#             - It is not a scientific or representative poll.

#         GENERAL CONSTRAINTS
#         - Use only the provided comments_json.
#         - Do not bring in outside facts or data.
#         - Do not mention the prompt or model behavior.
#         - Keep the whole answer compact, clear, and focused on the poll-style result.
#     """.strip()

#     completion = client.chat.completions.create(
#         model="gpt-5-2025-08-07",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": report_prompt}
#         ]
#     )
#     report_text = completion.choices[0].message.content
#     return report_text
# def results_curation(social_urls, comments_json, user_query):
#     # We still use social_urls only to build stats_text.
#     stats_text = summarize_platform_activity(social_urls, comments_json)

#     system_prompt = """
#         You are an expert opinion-poll statistician working with social media data.

#         Your job:
#         - Treat the provided comments_json as responses to an informal opinion poll about the user question.
#         - Use ONLY comments_json and stats_text. Do NOT ask the user for any numbers or options.
#         - From stats_text, you may extract:
#             - Total number of comments analyzed (total polled).
#             - Number of platforms and their names.
#             - Total number of posts per platform.
#         - In the main poll sections, use ONLY:
#             - Platforms (count + names).
#             - Total comments polled (across all platforms).
#         - Per-platform information (posts per platform) may ONLY appear in a final “Activity Summary” section, never in the main poll results.

#         - From the user question + comments_json, infer suitable answer OPTIONS:
#             - For example: Yes / No / Neutral
#             - Or Good / Bad / No opinion
#             - Or multiple textual answers (e.g., three or four distinct views).
#         - Classify comments into those options and compute an approximate percentage distribution.

#         Key principles:
#         - This is NOT a scientific or representative poll. It is only based on the analyzed social media comments.
#         - Focus on numbers and clear tabulation. Short, minimal commentary only.
#         - Do NOT provide per-platform percentages or per-platform comment counts anywhere.
#         - Use simple language. Be concise and to the point.
#     """.strip()

#     report_prompt = f"""
#         USER QUESTION
#         {user_query}

#         INPUT DATA — COMMENTS JSON
#         {json.dumps(comments_json, indent=2, ensure_ascii=False)}

#         INPUT DATA — STATS TEXT
#         {stats_text}

#         YOUR TASK

#         1) Infer Poll Options
#         - Treat the USER QUESTION as the poll question.
#         - Infer 2–5 clear answer OPTIONS that logically answer the question, using:
#             - The phrasing of the USER QUESTION.
#             - The patterns you see in the comments.
#         - Examples of option shapes (for guidance only, choose what fits best):
#             - Yes / No / Neutral
#             - Good / Bad / No opinion
#             - Support / Oppose / Neutral
#             - Several distinct textual answers (e.g., “They organize and manage elections”, “They decide who won”, “They make election laws”).
#         - Options must be mutually distinct and meaningful answers to the question.

#         2) Extract Platforms and Totals
#         - From STATS TEXT, extract:
#             - The number of platforms and their names (e.g., 4 platforms: FB, Instagram, TikTok, X).
#             - The total number of comments analyzed (total polled).
#             - The total number of posts per platform (for later use in the Activity Summary ONLY).
#         - In the main poll results, you must NOT show per-platform comment counts or percentages.

#         3) Compute Opinion Distribution
#         - Treat each comment in comments_json as one “vote”.
#         - Classify comments into the inferred OPTIONS.
#         - Compute approximate percentage share for each option:
#             - Use integer percentages that roughly sum to 100.
#             - If many comments are unclear or do not take a stance, include an option like “Neutral / No clear opinion”.
#         - If helpful, you may infer approximate counts per option as:
#             count ≈ (percentage / 100) × total polled
#           but keep the main focus on percentages.

#         OUTPUT FORMAT

#         Your response must be short and structured exactly as follows:

#         1) Poll Overview
#         - Question: <restate the user question in one clear sentence>
#         - Platforms: <number of platforms> — <comma-separated platform names>
#         - Total polled: <total number of comments>

#         2) Results (Percentages)
#         - List each option on its own line in this format:
#           - <Option text> — <P%>
#         - Use integer percentages that roughly sum to 100.
#         - Options should be clear, mutually distinct answers to the poll question.

#         3) Brief Comment
#         - 1–3 short sentences, maximum.
#         - State which option has the highest percentage and what that implies in simple terms.
#         - Keep it very concise and neutral (no deep analysis, just a plain-language summary of the numbers).

#         4) Activity Summary (Posts & Comments)
#         - Use ONLY STATS TEXT for this section.
#         - First, list the total number of posts per platform, one per line, like:
#           - <Platform name> — <N posts>
#         - Then add one final line:
#           - Total comments analyzed: <total number of comments>
#         - Do NOT provide per-platform comment counts here; only per-platform posts and overall comments.

#         CONSTRAINTS
#         - Use only comments_json and stats_text.
#         - Do NOT show per-platform comment counts or percentages anywhere.
#         - Do NOT ask the user for options, sample sizes, or any additional numbers.
#         - Do NOT call this a scientific poll. Call it an “informal social media opinion poll” or “informal opinion snapshot”.
#         - Keep everything compact, numeric, and to the point.
#     """.strip()

#     completion = client.chat.completions.create(
#         model="gpt-5-2025-08-07",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": report_prompt}
#         ]
#     )
#     report_text = completion.choices[0].message.content
#     return report_text
def results_curation(social_urls, comments_json, user_query):
    # We still use social_urls only to build stats_text.
    stats_text = summarize_platform_activity(social_urls, comments_json)

    system_prompt = """
        You are an expert opinion-poll statistician working with online public comments and posts.

        Your job:
        - Treat the provided comments_json as responses to an informal opinion poll about the user question.
        - Comments and posts may come from social media, forums, Google posts, Bing posts, or other online platforms.
        - Use ONLY comments_json and stats_text. Do NOT ask the user for any numbers or options.
        - From stats_text, you may extract:
            - Total number of comments analyzed (total polled).
            - Number of platforms and their names.
            - Total number of posts per platform.
        - In the main poll sections, use ONLY:
            - Platforms (count + names).
            - Total comments polled (across all platforms).
        - Per-platform information (posts per platform) may ONLY appear in a final “Activity Summary” section, never in the main poll results.

        - From the user question + comments_json, infer suitable answer OPTIONS:
            - For example: Yes / No / Neutral
            - Or Good / Bad / No opinion
            - Or multiple textual answers (e.g., three or four distinct views).
        - Classify comments into those options and compute an approximate percentage distribution.

        Key principles:
        - This is NOT a scientific or representative poll. It is only based on the analyzed online comments and posts.
        - Focus on numbers and clear tabulation. Short, minimal commentary only.
        - Do NOT provide per-platform percentages or per-platform comment counts anywhere.
        - Use simple language. Be concise and to the point.
    """.strip()

    report_prompt = f"""
        USER QUESTION
        {user_query}

        INPUT DATA — COMMENTS JSON
        {json.dumps(comments_json, indent=2, ensure_ascii=False)}

        INPUT DATA — STATS TEXT
        {stats_text}

        YOUR TASK

        1) Infer Poll Options
        - Treat the USER QUESTION as the poll question.
        - Infer 2–5 clear answer OPTIONS that logically answer the question, using:
            - The phrasing of the USER QUESTION.
            - The patterns you see in the comments and posts.
        - Examples of option shapes (for guidance only, choose what fits best):
            - Yes / No / Neutral
            - Good / Bad / No opinion
            - Support / Oppose / Neutral
            - Several distinct textual answers (e.g., “They organize and manage elections”, “They decide who won”, “They make election laws”).
        - Options must be mutually distinct and meaningful answers to the question.

        2) Extract Platforms and Totals
        - From STATS TEXT, extract:
            - The number of platforms and their names (e.g., 4 platforms: FB, Instagram, TikTok, X, Google, Bing, etc. — whatever is present).
            - The total number of comments analyzed (total polled).
            - The total number of posts per platform (for later use in the Activity Summary ONLY).
        - In the main poll results, you must NOT show per-platform comment counts or percentages.

        3) Compute Opinion Distribution
        - Treat each comment or post in comments_json as one “vote”.
        - Classify them into the inferred OPTIONS.
        - Compute approximate percentage share for each option:
            - Use integer percentages that roughly sum to 100.
            - If many items are unclear or do not take a stance, include an option like “Neutral / No clear opinion”.
        - If helpful, you may infer approximate counts per option as:
            count ≈ (percentage / 100) × total polled
          but keep the main focus on percentages.

        OUTPUT FORMAT

        Your response must be short and structured exactly as follows:

        1) Poll Overview
        - Question: <restate the user question in one clear sentence>
        - Platforms: <number of platforms> — <comma-separated platform names>
        - Total polled: <total number of comments>

        2) Results (Percentages)
        - List each option on its own line in this format:
          - <Option text> — <P%>
        - Use integer percentages that roughly sum to 100.
        - Options should be clear, mutually distinct answers to the poll question.

        3) Brief Comment
        - 3–4 short sentences, maximum.
        - State which option has the highest percentage and what that implies in simple terms.
        - Keep it concise and neutral (no deep analysis, just a plain-language summary of the numbers).

        4) Activity Summary (Posts & Comments)
        - Use ONLY STATS TEXT for this section.
        - First, list the total number of posts per platform, one per line, like:
          - <Platform name> — <N posts>
        - Then add one final line:
          - Total comments analyzed: <total number of comments>
        - Do NOT provide per-platform comment counts here; only per-platform posts and overall comments.

        CONSTRAINTS
        - Use only comments_json and stats_text.
        - Treat all platforms uniformly: social media, Google posts, Bing posts, forums, or others are all just “platforms”.
        - Do NOT show per-platform comment counts or percentages anywhere.
        - Do NOT ask the user for options, sample sizes, or any additional numbers.
        - Do NOT call this a scientific poll. Call it an “informal online opinion poll” or “informal opinion snapshot”.
        - Keep everything compact, numeric, and to the point.
    """.strip()

    completion = client.chat.completions.create(
        model="gpt-5-2025-08-07",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": report_prompt}
        ]
    )
    report_text = completion.choices[0].message.content
    return report_text


import json
import os
from dotenv import load_dotenv
from typing import Annotated, List, Optional, Dict, Any, Callable
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from BOL import serp_search
from urls_scrappers import collect_platform_urls
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from job_queue import JobManager, JobRecord

from BOL import ( reddit_comment_retrieval, youtube_post_retrieval, tiktok_post_retrieval,
                  instagram_comments_retrieval, facebook_comments_retrieval,
                  x_comments_retrieval,linkedin_comments_retrieval, results_curation)

load_dotenv()

BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")

# Initialize State
class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_question: Optional[str]
    max_per_platform: Optional[int]
    google_results: Optional[str]
    bing_results: Optional[str]
    platform_urls: Optional[Dict[str, List[str]]]
    # reddit_comments_data : Optional[List[str]]
    youtube_comments_data : Optional[List[str]]
    tiktok_comments_data : Optional[List[str]]
    instagram_comments_data : Optional[List[str]]
    facebook_comments_data : Optional[List[str]]
    x_comments_data : Optional[List[str]]
    linkedin_comments_data : Optional[List[str]]
    ready :  Optional[bool]
    combined_comments : Optional[dict]
    # comments_metadata : Optional[List[str]]
    final_results : Optional[List[str]]

    
# Google Search
def google_search(state: State):
    print("Getting Google Post")
    user_question = state.get("user_question", "")
    google_results = serp_search(user_question, engine="google")
    return {"google_results": google_results} 

# Bing Search
def bing_search(state: State):
    print("Getting Bing Post")
    user_question = state.get("user_question", "")
    bing_results = serp_search(user_question, engine="bing")
    return {"bing_results": bing_results}

# Social Media URLs
def social_media_urls(state: State):
    user_question = state.get("user_question", "")
    max_per_platform = state.get("max_per_platform", None)
    platform_urls = collect_platform_urls(user_question, max_per_platform)
    return {"platform_urls": platform_urls}

# Reddit comments
# def retrieve_reddit_comments(state: State):
#     selected_urls = state.get("platform_urls", {})
#     reddit_urls = selected_urls.get("Reddit", [])
#     print("Getting Reddit post comments")
#     if not reddit_urls:
#         return {"reddit_comments_data": []}
#     reddit_comments_data = reddit_comment_retrieval(reddit_urls,days_back=10, load_all_replies=False, comment_limit=5)
#     if reddit_comments_data:
#         print(f"Successfully got {len(reddit_comments_data)} Reddit posts")
#     else:
#         print("Failed to get Reddit post data")
#         reddit_comments_data = []
#     return {"reddit_comments_data":reddit_comments_data}

#Youtube Comments
def retrieve_youtube_comments(state: State):
    selected_urls = state.get("platform_urls", {})
    youtube_urls = selected_urls.get("Youtube", [])
    print("Getting youtube post comments")
    if not youtube_urls:
        return {"youtube_comments_data": []}

    youtube_comments_data = youtube_post_retrieval(youtube_urls)

    if youtube_comments_data:
        print(f"Successfully got {len(youtube_comments_data)} Youtube comments")
    else:
        print("Failed to get Youtube comments data")
        youtube_comments_data = []

    return {"youtube_comments_data": youtube_comments_data}

#Tiktok Comments
def retrieve_tiktok_comments(state: State):
    selected_urls = state.get("platform_urls", {})
    tiktok_urls = selected_urls.get("Tiktok", [])
    print("Getting Tiktok post comments")

    if not tiktok_urls:
        return {"tiktok_comments_data": []}
    
    tiktok_urls = tiktok_urls[:1]

    tiktok_comments_data = tiktok_post_retrieval(tiktok_urls)

    if tiktok_comments_data:
        print(f"Successfully got {len(tiktok_comments_data)} Tiktok posts")
    else:
        print("Failed to get Tiktok post data")
        tiktok_comments_data = []

    return {"tiktok_comments_data":tiktok_comments_data}

# Instagram Comments
def retrieve_instagram_comments(state: State):
    selected_urls = state.get("platform_urls", {})
    instagram_urls = selected_urls.get("Instagram", [])
    print("Getting Instagram post comments")

    instagram_comments_data = instagram_comments_retrieval(instagram_urls)

    if instagram_comments_data:
        print(f"Successfully got {len(instagram_comments_data)} Instagram posts")
    else:
        print("Failed to get Instagram post data")
        instagram_comments_data = []

    return {"instagram_comments_data":instagram_comments_data}

# Facebook Comments
def retrieve_facebook_comments(state: State):
    selected_urls = state.get("platform_urls", {})
    facebook_urls = selected_urls.get("Facebook", [])
    print("Getting facebook post comments")

    facebook_comments_data = facebook_comments_retrieval(facebook_urls, get_all_replies=False, limit_records=5, comments_sort="Most relevant")

    if facebook_comments_data:
        print(f"Successfully got {len(facebook_comments_data)} Facebook posts")
    else:
        print("Failed to get Facebook post data")
        facebook_comments_data = []

    return {"facebook_comments_data":facebook_comments_data}

# X Comments
def retrieve_x_comments(state: State):
    selected_urls = state.get("platform_urls", {})
    x_urls = selected_urls.get("X", [])
    print("Getting x post comments")

    x_comments_data = x_comments_retrieval(x_urls)

    if x_comments_data:
        print(f"Successfully got {len(x_comments_data)} X posts")
    else:
        print("Failed to get X post data")
        x_comments_data = []

    return {"x_comments_data":x_comments_data}

# LinkedIn Comments
def retrieve_linkedin_comments(state: State):
    selected_urls = state.get("platform_urls", {})
    linkedin_urls = selected_urls.get("LinkedIn", [])
    print("Getting Linkedin comments")

    linkedin_comments_data = linkedin_comments_retrieval(linkedin_urls)

    if linkedin_comments_data:
        print(f"Successfully got {len(linkedin_comments_data)} LinkedIn posts")
    else:
        print("Failed to get LinkedIn post data")
        linkedin_comments_data = []

    return {"linkedin_comments_data":linkedin_comments_data}

# def social_comments(state: State):
#     # Check if all sources have returned data
#     if all([
#         # state.get("reddit_comments_data"),
#         state.get("youtube_comments_data"),
#         state.get("tiktok_comments_data"),
#         state.get("instagram_comments_data"),
#         state.get("facebook_comments_data"),
#         state.get("x_comments_data"),
#         state.get("linkedin_comments_data")
#     ]):
#         # Proceed to combining comments
#         return {"ready": True}
#     else:
#         # Not all comments arrived yet; wait
#         return {"ready": False}
def social_comments(state: State):
    keys = [
        "youtube_comments_data",
        "tiktok_comments_data",
        "instagram_comments_data",
        "facebook_comments_data",
        "x_comments_data",
        "linkedin_comments_data",
    ]
    # Ready once every key is set by its fetcher (None -> done), regardless of [] vs list
    ready = all(state.get(k) is not None for k in keys)
    return {"ready": ready}

    
def combine_comments(state: State):
    combined_comments = {
        # "Reddit": state.get("reddit_comments_data", []),
        "Youtube": state.get("youtube_comments_data", []),
        "Tiktok": state.get("tiktok_comments_data", []),
        "Instagram": state.get("instagram_comments_data", []),
        "Facebook": state.get("facebook_comments_data", []),
        "X": state.get("x_comments_data", []),
        "LinkedIn": state.get("linkedin_comments_data", []),
        "Google" : state.get("google_results", []),
        "Bing" : state.get("bing_results", [])
    }
    print("Combined all platform comments.")
    return {"combined_comments": combined_comments}

# def comments_metadata(state: State):
#     selected_urls = state.get("platform_urls", {})
#     return selected_urls

def final_output(state: State):
    selected_urls = state.get("platform_urls", {})
    combined_comments = state.get("combined_comments", {})
    user_question= state.get("user_question",str)
    final_results= results_curation(selected_urls,combined_comments,user_question)
    return {"final_results": final_results}


# def route_if_ready(state: State):
#     return "combine_comments" if state.get("ready") else None 

def route_if_ready(state: State):
    # Only proceed once every retrieval node has *finished* (even if it found nothing)
    if state.get("ready"):
        return ["combine_comments"]   # <- list, not string
    return []

# Initialize graph
graph_builder = StateGraph(State)

graph_builder.add_node("google_search", google_search)
graph_builder.add_node("bing_search", bing_search)
graph_builder.add_node("social_media_urls", social_media_urls)

# graph_builder.add_node("retrieve_reddit_comments", retrieve_reddit_comments)
graph_builder.add_node("retrieve_youtube_comments", retrieve_youtube_comments)
graph_builder.add_node("retrieve_tiktok_comments", retrieve_tiktok_comments)
graph_builder.add_node("retrieve_instagram_comments", retrieve_instagram_comments)
graph_builder.add_node("retrieve_facebook_comments", retrieve_facebook_comments)
graph_builder.add_node("retrieve_x_comments", retrieve_x_comments)
graph_builder.add_node("retrieve_linkedin_comments", retrieve_linkedin_comments)
graph_builder.add_node("social_comments", social_comments)
graph_builder.add_node("combine_comments", combine_comments)
graph_builder.add_node("final_results", final_output)
# graph_builder.add_node("comments_metadata", comments_metadata)

graph_builder.add_edge(START, "google_search")
graph_builder.add_edge(START, "bing_search")
graph_builder.add_edge(START, "social_media_urls")


# graph_builder.add_edge("social_media_urls", "retrieve_reddit_comments")
graph_builder.add_edge("social_media_urls", "retrieve_youtube_comments")
graph_builder.add_edge("social_media_urls", "retrieve_tiktok_comments")
graph_builder.add_edge("social_media_urls", "retrieve_instagram_comments")
graph_builder.add_edge("social_media_urls", "retrieve_facebook_comments")
graph_builder.add_edge("social_media_urls", "retrieve_x_comments")
graph_builder.add_edge("social_media_urls", "retrieve_linkedin_comments")

graph_builder.add_edge("retrieve_youtube_comments", "social_comments")
graph_builder.add_edge("retrieve_tiktok_comments", "social_comments")
graph_builder.add_edge("retrieve_instagram_comments", "social_comments")
graph_builder.add_edge("retrieve_facebook_comments", "social_comments")
graph_builder.add_edge("retrieve_x_comments", "social_comments")
graph_builder.add_edge("retrieve_linkedin_comments", "social_comments")

graph_builder.add_conditional_edges(
    "social_comments",
    route_if_ready,
    {"combine_comments": "combine_comments"},
)
graph_builder.add_edge("google_search", "combine_comments")
graph_builder.add_edge("bing_search", "combine_comments")
graph_builder.add_edge("combine_comments", "final_results")
graph_builder.add_edge("final_results", END)

graph = graph_builder.compile()

# ==========================
#   RESEARCH WRAPPER
# ==========================

def perform_research(user_question: str, max_per_platform: int) -> List[str]:
    """
    Runs the graph once for a single question, without storing or using history.
    Returns final curated results (list/strings as produced by results_curation).
    """
    print("\nStarting parallel research process...")
    print("Launching Google, Bing, LinkedIn, Instagram, X, TikTok, YouTube, Facebook...\n")

    state: State = {
        "messages": [{"role": "user", "content": user_question}],
        "user_question": user_question,
        "max_per_platform": max_per_platform,
        "google_results": None,
        "bing_results": None,
        "platform_urls": None,
        "youtube_comments_data": None,
        "tiktok_comments_data": None,
        "instagram_comments_data": None,
        "facebook_comments_data": None,
        "x_comments_data": None,
        "linkedin_comments_data": None,
        "ready": None,
        "combined_comments": None,
        "final_results": None,
    }
    final_state = graph.invoke(state)
    return final_state.get("final_results", [])


# ==========================
#   FASTAPI PART
# ==========================

app = FastAPI(
    title="Opinion Poll API",
    description="Batch opinion polling (1–5 questions) over web & social media",
    version="1.0.0",
)

# Optional: allow all origins (useful for dev / Postman / frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Request & Response Models ----

class OpinionPollRequest(BaseModel):
    questions: List[str]          # 1 to 5 questions
    max_per_platform: int = 3     # how many posts per platform


class OpinionAnswer(BaseModel):
    index: int
    question: str
    results: List[str]


class OpinionPollResponse(BaseModel):
    answers: List[OpinionAnswer]


# ---- MAIN ENDPOINT: /opinion_poll ----

@app.post("/opinion_poll", response_model=OpinionPollResponse)
def opinion_poll(req: OpinionPollRequest):
    # Clean empty questions, enforce 1–5
    cleaned_questions = [q.strip() for q in req.questions if q and q.strip()]

    if not cleaned_questions:
        raise HTTPException(status_code=400, detail="At least one non-empty question is required.")

    if len(cleaned_questions) > 5:
        cleaned_questions = cleaned_questions[:5]

    answers: List[OpinionAnswer] = []

    for idx, q in enumerate(cleaned_questions, start=1):
        results = perform_research(q, req.max_per_platform)
        if not isinstance(results, list):
            results = [str(results)]

        answers.append(
            OpinionAnswer(
                index=idx,
                question=q,
                results=results
            )
        )

    return OpinionPollResponse(answers=answers)


# ==========================
#   DEV ENTRYPOINT
# ==========================

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
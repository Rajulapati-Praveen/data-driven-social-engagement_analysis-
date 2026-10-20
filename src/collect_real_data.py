"""
Module 1: Content Performance Tracker (Data Extraction Engine) - REAL data collection.

Two official, ToS-compliant options (preferred over scraping):

A) YouTube Data API v3   (free key from console.cloud.google.com -> enable "YouTube Data API v3")
     python -m src.collect_real_data youtube --api-key YOUR_KEY --channel-id UCxxxx
   Gives: views, likes, comments, duration + comment text.
   LIMITATION: YouTube's public API does NOT expose shares/saves/retention (those are in YouTube Studio
   analytics -> export the CSV and merge it in). Missing columns are left blank and cleaned later.

B) Instagram Graph API   (needs an Instagram Business/Creator account linked to a Facebook Page,
   and an access token from developers.facebook.com)
     python -m src.collect_real_data instagram --token YOUR_TOKEN --ig-user-id 1784xxxx
   Gives: likes, comments, shares, saved, reach, plays (Reels) -> the full "Shares/Saves" data.

Both write data/raw/posts_raw.csv and comments_raw.csv in the same schema the pipeline expects.
You must still add the columns `topic`, `format`, `hook_type`, `caption_style` yourself
(a simple spreadsheet tagging each post) - these are YOUR content labels.

NOTE: This file was written against the public API docs but needs YOUR credentials, so it
has not been run live here. Web scraping (Selenium/BeautifulSoup) of Instagram is against its
Terms of Service - use the official API for your own account.
"""
import argparse
import re
import requests
import pandas as pd
from .config import RAW


def _iso_to_seconds(d):
    m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", d)
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0) if m else None


def youtube(api_key, channel_id, max_videos=100):
    base = "https://www.googleapis.com/youtube/v3"
    ids, token = [], None
    while len(ids) < max_videos:
        r = requests.get(f"{base}/search", params=dict(key=api_key, channelId=channel_id, part="id",
                         type="video", order="date", maxResults=50, pageToken=token)).json()
        ids += [i["id"]["videoId"] for i in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    posts, comments = [], []
    for i in range(0, len(ids), 50):
        r = requests.get(f"{base}/videos", params=dict(key=api_key, part="snippet,statistics,contentDetails",
                         id=",".join(ids[i:i + 50]))).json()
        for v in r.get("items", []):
            st, sn = v["statistics"], v["snippet"]
            dt = pd.to_datetime(sn["publishedAt"]).tz_convert("Asia/Kolkata")  # IST
            dur = _iso_to_seconds(v["contentDetails"]["duration"])
            posts.append(dict(content_id=v["id"], post_date=dt.date(), post_hour=dt.hour, title=sn["title"],
                              duration_sec=dur, format="Short" if dur and dur <= 60 else "Long",
                              views=int(st.get("viewCount", 0)), likes=int(st.get("likeCount", 0)),
                              comments=int(st.get("commentCount", 0)), shares=None, saves=None,
                              retention_rate=None, followers_gained=None,
                              topic=None, hook_type=None, caption_style=None))
    for vid in ids:
        r = requests.get(f"{base}/commentThreads", params=dict(key=api_key, videoId=vid, part="snippet",
                         maxResults=100, textFormat="plainText")).json()
        for it in r.get("items", []):
            s = it["snippet"]["topLevelComment"]
            comments.append(dict(comment_id=s["id"], content_id=vid, comment_text=s["snippet"]["textDisplay"]))
    return pd.DataFrame(posts), pd.DataFrame(comments)


def instagram(token, ig_user_id, limit=100):
    base = "https://graph.facebook.com/v21.0"
    media = requests.get(f"{base}/{ig_user_id}/media", params=dict(
        access_token=token, limit=limit,
        fields="id,caption,media_type,media_product_type,timestamp,like_count,comments_count")).json().get("data", [])
    posts, comments = [], []
    for m in media:
        ins = requests.get(f"{base}/{m['id']}/insights", params=dict(
            access_token=token, metric="reach,saved,shares,total_interactions")).json().get("data", [])
        met = {i["name"]: i["values"][0]["value"] for i in ins}
        dt = pd.to_datetime(m["timestamp"]).tz_convert("Asia/Kolkata")  # IST
        posts.append(dict(content_id=m["id"], post_date=dt.date(), post_hour=dt.hour, caption=m.get("caption"),
                          views=met.get("reach"), likes=m.get("like_count"), comments=m.get("comments_count"),
                          shares=met.get("shares"), saves=met.get("saved"), retention_rate=None,
                          followers_gained=None, duration_sec=None, format=None,
                          topic=None, hook_type=None, caption_style=None))
        for c in requests.get(f"{base}/{m['id']}/comments", params=dict(access_token=token, limit=100)).json().get("data", []):
            comments.append(dict(comment_id=c["id"], content_id=m["id"], comment_text=c.get("text", "")))
    return pd.DataFrame(posts), pd.DataFrame(comments)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="src", required=True)
    y = sub.add_parser("youtube"); y.add_argument("--api-key", required=True); y.add_argument("--channel-id", required=True)
    i = sub.add_parser("instagram"); i.add_argument("--token", required=True); i.add_argument("--ig-user-id", required=True)
    a = ap.parse_args()
    p, c = youtube(a.api_key, a.channel_id) if a.src == "youtube" else instagram(a.token, a.ig_user_id)
    p.to_csv(RAW / "posts_raw.csv", index=False)
    c.to_csv(RAW / "comments_raw.csv", index=False)
    print(f"Saved {len(p)} posts and {len(c)} comments to data/raw/. Now fill topic/hook_type/caption_style, "
          "add data/raw/trends_raw.csv, then run: python run_pipeline.py --real")

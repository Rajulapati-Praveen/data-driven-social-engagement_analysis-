"""
STEP 1 (practice data).  Creates a realistic *simulated* dataset so the whole project runs
without needing API keys.  Real accounts can be plugged in later with collect_real_data.py.

Outputs (data/raw):
  posts_raw.csv     - one row per piece of content (the "Content Series")
  comments_raw.csv  - user comments on those posts
  trends_raw.csv    - weekly search/hashtag interest for external keywords

Hidden "true effects" are baked in (e.g. Social Anxiety content goes more viral, short videos
get more shares, evening posts do better) so your statistical modules have something real to find.
"""
import numpy as np
import pandas as pd
from .config import RAW, RANDOM_SEED

rng = np.random.default_rng(RANDOM_SEED)

TOPICS = {  # topic -> hidden virality multiplier
    "Social Anxiety": 1.55, "Loneliness": 1.40, "Overthinking": 1.30, "Burnout": 1.25,
    "Friendship": 1.10, "Career Confusion": 1.00, "Body Image": 1.00, "Dating": 0.85,
}
FORMATS = ["Short", "Long"]
HOOKS = ["Visual", "Text"]
CAPTIONS = ["Question", "Story", "Listicle"]

RELATABLE_PARTS = [
    "omg this is so me", "me too, I thought I was the only one", "I feel this so hard",
    "needed this today", "this is literally my life", "same here, every single day",
    "finally someone gets it", "I relate to this so much", "felt this in my soul",
    "this is exactly how I feel", "why is this so true", "I thought it was just me",
    "I've been there, thank you for saying it", "saving this for later, I needed to hear it",
    "sending this to my best friend", "you just described me",
]
NEUTRAL_PARTS = [
    "nice video", "good editing", "what camera do you use", "first", "interesting topic",
    "can you make a video on productivity", "great lighting", "how long did this take to make",
    "okay", "check out my page", "which app is this", "what song is this", "hello from India",
    "cool", "thanks for sharing", "the audio is a bit low",
]
EMOJIS = ["", "", "", " 😭", " 🥺", " ❤️", " 😅", " 💯", " 🙏"]


def make_posts(n=220):
    start = pd.Timestamp("2026-01-05")
    rows = []
    topic_names = list(TOPICS)
    for i in range(n):
        date = start + pd.Timedelta(days=int(i * 190 / n)) + pd.Timedelta(hours=int(rng.integers(0, 3)))
        topic = rng.choice(topic_names)
        fmt = rng.choice(FORMATS, p=[0.55, 0.45])
        hook = rng.choice(HOOKS)
        caption = rng.choice(CAPTIONS)
        hour = int(rng.choice(range(7, 24), p=_hour_probs()))
        duration = int(rng.integers(12, 35) if fmt == "Short" else rng.integers(45, 140))

        # --- hidden effects ---
        reach_base = 3000 * (1 + i / n * 0.8)  # account slowly grows
        evening = 1.25 if 19 <= hour <= 22 else 1.0
        views = reach_base * rng.lognormal(0, 0.45) * evening * (1.1 if hook == "Visual" else 1.0)
        views = int(views)
        retention = np.clip(rng.normal(0.62 if fmt == "Short" else 0.41, 0.09)
                            + (0.03 if hook == "Visual" else 0), 0.08, 0.98)
        t = TOPICS[topic]
        share_rate = 0.012 * t * (1.3 if fmt == "Short" else 0.9) * rng.lognormal(0, 0.25)
        save_rate = 0.020 * t * (1.2 if hook == "Text" else 1.0) * (1.25 if caption == "Listicle" else 1.0) * rng.lognormal(0, 0.25)
        like_rate = 0.06 * rng.lognormal(0, 0.2)
        comment_rate = 0.006 * (1.2 if caption == "Question" else 1.0) * rng.lognormal(0, 0.3)

        shares, saves = int(views * share_rate), int(views * save_rate)
        likes, comments = int(views * like_rate), int(views * comment_rate)
        followers_gained = int(max(0, (shares * 0.35 + saves * 0.18) * rng.lognormal(0, 0.3)))
        rows.append(dict(
            content_id=f"C{i+1:04d}", post_date=date.date(), post_hour=hour, topic=topic,
            format=fmt, hook_type=hook, caption_style=caption, duration_sec=duration,
            views=views, likes=likes, comments=comments, shares=shares, saves=saves,
            retention_rate=round(float(retention), 3), followers_gained=followers_gained,
        ))
    df = pd.DataFrame(rows)

    # Make the data "dirty" like real scraped data (so the cleaning step has work to do)
    dirty = df.sample(6, random_state=1).index
    df.loc[dirty[:3], "saves"] = np.nan
    df.loc[dirty[3:5], "retention_rate"] = np.nan
    df.loc[dirty[5], "views"] = -1
    df = pd.concat([df, df.sample(4, random_state=2)], ignore_index=True)  # duplicates
    df["topic"] = df["topic"].where(rng.random(len(df)) > 0.03, df["topic"].str.lower())  # inconsistent case
    return df


def _hour_probs():
    w = np.array([1, 1, 1, 1.5, 2, 2, 2, 2, 2, 2, 2.5, 3, 3.5, 4, 5, 5, 4])  # 7h..23h
    return w / w.sum()


def make_comments(posts):
    clean = posts.drop_duplicates("content_id")
    rows, cid = [], 1
    for _, p in clean.iterrows():
        topic = str(p["topic"]).title()
        emotional = TOPICS.get(topic, 1.0)
        p_rel = np.clip(0.18 + 0.30 * (emotional - 0.85), 0.05, 0.85)
        n = int(min(18, max(3, (p["comments"] if p["comments"] > 0 else 20) / 6)))
        for _ in range(n):
            relatable = rng.random() < p_rel
            text = rng.choice(RELATABLE_PARTS if relatable else NEUTRAL_PARTS) + rng.choice(EMOJIS)
            if relatable and rng.random() < 0.3:
                text = f"{text}. {rng.choice(RELATABLE_PARTS)}"
            rows.append(dict(comment_id=f"M{cid:06d}", content_id=p["content_id"], comment_text=text,
                             true_label="Relatable" if relatable else "Neutral"))
            cid += 1
    return pd.DataFrame(rows)


def make_trends(weeks=40):
    kws = {"social anxiety tips": 0.5, "quiet quitting": -0.4, "overthinking at night": 1.2,
           "loneliness in your 20s": 0.9, "situationship": 0.1, "burnout recovery": 0.6,
           "friend breakup": 0.15, "body neutrality": 0.3}
    idx = pd.date_range(end="2026-10-05", periods=weeks, freq="W-MON")
    rows = []
    for k, slope in kws.items():
        base = 40 + rng.normal(0, 3)
        for w, d in enumerate(idx):
            val = base + slope * w + 6 * np.sin(w / 4) + rng.normal(0, 3)
            if k == "friend breakup" and w > weeks - 12:  # emerging trend (accelerating)
                val += (w - (weeks - 12)) ** 1.3
            rows.append(dict(week=d.date(), keyword=k, interest=float(np.clip(val, 1, 100))))
    return pd.DataFrame(rows)


def main():
    posts = make_posts()
    comments = make_comments(posts)
    trends = make_trends()
    posts.to_csv(RAW / "posts_raw.csv", index=False)
    comments.to_csv(RAW / "comments_raw.csv", index=False)
    trends.to_csv(RAW / "trends_raw.csv", index=False)
    print(f"[generate_data] posts={len(posts)} comments={len(comments)} trend_rows={len(trends)}")


if __name__ == "__main__":
    main()

"""
Auto-labeller: guesses the three label columns from each video's TITLE, so you don't type 100 rows by hand.

    python -m src.auto_label

What it does
  1. Backs up your original file to data/raw/posts_raw_original.csv (first run only).
  2. Drops videos newer than 7 days (their numbers are still growing, which would distort the analysis).
  3. Fills `topic`, `hook_type`, `caption_style` ONLY where they are empty (anything you typed by hand is kept).
  4. Saves a human-friendly file  data/raw/labels_to_review.csv  - open it in Excel, correct wrong guesses,
     then run:   python -m src.auto_label --apply

These are GUESSES from simple keyword rules. YouTube does not tell us the real hook or topic, so
always skim the results and fix mistakes - and say in your report that labels were rule-assisted.
Edit the TOPIC_KEYWORDS dictionary below to match your own content.
"""
import re
import sys
import shutil
import pandas as pd
from .config import RAW

MIN_AGE_DAYS = 7

# topic -> keywords found in the title / hashtags (lower case). First topic with the most hits wins.
TOPIC_KEYWORDS = {
    # --- "relatable struggle" topics (your own content series) ---
    "Social Anxiety": ["social anxiety", "anxious", "anxiety", "awkward", "shy", "nervous"],
    "Loneliness": ["lonely", "loneliness", "alone", "no friends", "isolated"],
    "Overthinking": ["overthink", "overthinking", "can't stop thinking", "thinking too much"],
    "Burnout": ["burnout", "burnt out", "exhausted", "tired of", "drained"],
    "Dating": ["dating", "crush", "relationship", "situationship", "breakup", "ex "],
    "Friendship": ["friend", "friendship", "bestie"],
    "Career Confusion": ["career", "job search", "what to do after", "confused about", "future"],
    "Body Image": ["body image", "insecure", "looks", "weight"],
    # --- topics for a tech/AI practice channel ---
    "AI & ChatGPT": ["ai ", " ai", "chatgpt", "gemini", "claude", "gpt", "llm", "prompt", "machine learning", "genai"],
    "Coding": ["coding", "programming", "python", "java", "developer", "react", "web dev", "code", "sql", "html"],
    "Tech Careers": ["salary", "jobs", "job ", "interview", "resume", "placement", "fresher", "internship", "tech careers"],
    "Data Science": ["data science", "data analyst", "data analytics", "power bi", "excel", "tableau"],
    "Tools & Tutorials": ["tutorial", "how to", "explained", "beginner", "guide", "course", "roadmap"],
}


def guess_topic(title: str) -> str:
    t = f" {str(title).lower()} "
    scores = {topic: sum(t.count(k) for k in kws) for topic, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def guess_hook(title: str) -> str:
    """Visual = title starts with an emoji/symbol (thumbnail-style hook); otherwise Text."""
    t = str(title).strip()
    return "Visual" if t and not re.match(r"[A-Za-z0-9\"'(\[]", t[0]) else "Text"


def guess_caption(title: str) -> str:
    t = str(title).lower()
    if "?" in t or re.match(r"\s*(why|how|what|is|are|can|do|does|should)\b", t):
        return "Question"
    if re.search(r"\b(top|best)?\s*\d+\s*(ways|tips|reasons|steps|mistakes|things|skills|tools|signs|careers|apps)\b", t) \
            or re.search(r"\btop\s*\d+\b|\b\d+\s+\w+\s+(that|to|you)\b", t):
        return "Listicle"
    if re.search(r"\b(my|i |i'm|i've|story|journey|when i|how i)\b", t):
        return "Story"
    return "Statement"


def main(apply_only=False):
    path = RAW / "posts_raw.csv"
    backup = RAW / "posts_raw_original.csv"
    review = RAW / "labels_to_review.csv"

    if apply_only:
        if not review.exists():
            sys.exit("labels_to_review.csv not found. Run  python -m src.auto_label  first.")
        edited = pd.read_csv(review)
        df = pd.read_csv(path)
        df = df.drop(columns=["topic", "hook_type", "caption_style"], errors="ignore") \
               .merge(edited[["content_id", "topic", "hook_type", "caption_style"]], on="content_id", how="left")
        df.to_csv(path, index=False)
        print(f"[auto_label] applied your reviewed labels to {len(df)} posts in posts_raw.csv")
        return

    if not backup.exists():
        shutil.copy(path, backup)
        print(f"[auto_label] backup saved: {backup.name}")
    df = pd.read_csv(backup)  # always start from the untouched original

    # drop very new videos
    age = (pd.Timestamp.now().normalize() - pd.to_datetime(df["post_date"])).dt.days
    old_enough = df[age >= MIN_AGE_DAYS]
    if len(old_enough) >= 10:
        print(f"[auto_label] dropped {len(df) - len(old_enough)} videos newer than {MIN_AGE_DAYS} days")
        df = old_enough.copy()
    else:
        print(f"[auto_label] WARNING: fewer than 10 videos are older than {MIN_AGE_DAYS} days - keeping all.")

    title = df["title"] if "title" in df.columns else df.get("caption", pd.Series([""] * len(df), index=df.index))
    for col, fn in [("topic", guess_topic), ("hook_type", guess_hook), ("caption_style", guess_caption)]:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = df[col].where(df[col].notna(), title.map(fn))

    df.to_csv(path, index=False)
    df[["content_id", "title", "topic", "hook_type", "caption_style"]].to_csv(review, index=False)
    print(f"[auto_label] labelled {len(df)} posts. Label counts:")
    for col in ["topic", "hook_type", "caption_style"]:
        print(f"  {col}: " + ", ".join(f"{k}={v}" for k, v in df[col].value_counts().items()))
    print("\nNext: open data/raw/labels_to_review.csv in Excel, fix wrong labels, save, then run:\n"
          "  python -m src.auto_label --apply\n  python run_pipeline.py --real")


if __name__ == "__main__":
    main(apply_only="--apply" in sys.argv)

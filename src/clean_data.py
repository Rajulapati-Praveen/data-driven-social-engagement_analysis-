"""
STEP 2. Data cleaning + loading into a SQL database (Deliverable 2: Structured Dataset).

Cleaning steps:
  1. remove duplicate posts / comments
  2. standardise text (topic names -> Title Case)
  3. drop impossible values (negative views)
  4. fill missing numbers (median per topic) and clip retention to 0-1
  5. add engineered columns (engagement metrics, day of week, time-of-day bucket)

Database: SQLite is used so the project runs anywhere with zero setup.
To use PostgreSQL / MySQL instead, replace `get_engine()` with e.g.
  sqlalchemy.create_engine("postgresql://user:password@localhost:5432/engagement")
"""
import re
import sqlite3
import pandas as pd
from .config import RAW, PROCESSED, DB_PATH, VIRAL_WEIGHTS


def clean_posts(df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)
    df = df.drop_duplicates(subset="content_id").copy()

    # --- make sure every expected column exists and numbers are really numbers ---
    int_cols = ["views", "likes", "comments", "shares", "saves", "followers_gained"]
    for col in int_cols + ["retention_rate", "duration_sec", "post_hour"]:
        if col not in df.columns:
            df[col] = float("nan")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["topic", "hook_type", "caption_style"]:
        if col not in df.columns:
            df[col] = float("nan")
        df[col] = df[col].fillna("Unlabelled")
    if "format" not in df.columns:
        df["format"] = float("nan")
    df["format"] = df["format"].fillna(
        pd.Series(["Short" if (d and d <= 60) else "Long" for d in df["duration_sec"].fillna(0)], index=df.index))

    df["topic"] = df["topic"].astype(str).str.strip().str.title()
    df = df[df["views"] > 0].copy()

    for col in ["likes", "comments", "shares", "saves"]:
        if df[col].isna().all():
            print(f"[clean] WARNING: column '{col}' is completely empty (the API did not provide it). "
                  f"Filled with 0 - add it by hand from the platform analytics if you can.")
            df[col] = 0
        df[col] = df[col].fillna(df.groupby("topic")[col].transform("median")).fillna(df[col].median()).fillna(0)
    df["followers_gained"] = df["followers_gained"].fillna(0)
    if df["retention_rate"].isna().all():
        print("[clean] WARNING: retention_rate is empty - left blank (add it from YouTube Studio / Instagram Insights).")
    else:
        df["retention_rate"] = df["retention_rate"].fillna(
            df.groupby("format")["retention_rate"].transform("median")).fillna(df["retention_rate"].median())
    df["retention_rate"] = df["retention_rate"].clip(0, 1)
    df[int_cols] = df[int_cols].round().astype(int)
    df["post_hour"] = df["post_hour"].fillna(12).astype(int)

    df["post_date"] = pd.to_datetime(df["post_date"])
    df["day_of_week"] = df["post_date"].dt.day_name()
    df["week"] = df["post_date"].dt.to_period("W").dt.start_time
    df["time_slot"] = pd.cut(df["post_hour"], bins=[-1, 11, 16, 18, 23],
                             labels=["Morning", "Afternoon", "Early Evening", "Prime Evening"]).astype(str)
    df["is_evening"] = df["post_hour"].between(19, 22)
    df["engagement_rate"] = (df["likes"] + df["comments"] + df["shares"] + df["saves"]) / df["views"]
    df["save_to_share_ratio"] = df["saves"] / df["shares"].replace(0, float("nan"))
    df["save_to_share_ratio"] = df["save_to_share_ratio"].astype(float)
    print(f"[clean] posts: {n0} -> {len(df)} rows")
    return df.reset_index(drop=True)


def clean_text(t: str) -> str:
    t = str(t).lower().strip()
    t = re.sub(r"http\S+", "", t)
    return re.sub(r"\s+", " ", t)


def clean_comments(df: pd.DataFrame, valid_ids) -> pd.DataFrame:
    n0 = len(df)
    df = df.drop_duplicates(subset="comment_id").copy()
    df = df[df["content_id"].isin(valid_ids)]
    df["clean_text"] = df["comment_text"].map(clean_text)
    df = df[df["clean_text"].str.len() > 0]
    print(f"[clean] comments: {n0} -> {len(df)} rows")
    return df.reset_index(drop=True)


def main():
    posts = clean_posts(pd.read_csv(RAW / "posts_raw.csv"))
    comments = clean_comments(pd.read_csv(RAW / "comments_raw.csv"), posts["content_id"])
    if not (RAW / "trends_raw.csv").exists():
        from .generate_data import make_trends
        print("[clean] NOTE: data/raw/trends_raw.csv not found - creating PRACTICE trend data. "
              "Replace it with Google Trends data (columns: week, keyword, interest).")
        make_trends().to_csv(RAW / "trends_raw.csv", index=False)
    trends = pd.read_csv(RAW / "trends_raw.csv", parse_dates=["week"])

    posts.to_csv(PROCESSED / "posts_clean.csv", index=False)
    comments.to_csv(PROCESSED / "comments_clean.csv", index=False)
    trends.to_csv(PROCESSED / "trends_clean.csv", index=False)

    with sqlite3.connect(DB_PATH) as con:
        posts.to_sql("posts", con, if_exists="replace", index=False)
        comments.to_sql("comments", con, if_exists="replace", index=False)
        trends.to_sql("trends", con, if_exists="replace", index=False)
    print(f"[clean] saved CSVs to data/processed and tables to {DB_PATH.name}")


if __name__ == "__main__":
    main()

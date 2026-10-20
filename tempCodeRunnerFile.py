
@st.cache_data
def load():
    posts = pd.read_csv(PROCESSED / "posts_scored.csv", parse_dates=["post_date", "week"])
    return dict(
        posts=posts,
        comments=pd.read_csv(PROCESSED / "comments_tagged.csv"),
        ranking=pd.read_csv(PROCESSED / "topic_ranking.csv"),
        ab=pd.read_csv(PROCESSED / "ab_test_results.csv"),
        recs=pd.read_csv(PROCESSED / "weekly_recommendations.csv"),
        trends=pd.read_csv(PROCESSED / "trends_clean.csv", parse_dates=["week"]),
        trend_sum=pd.read_csv(PROCESSED / "trend_summary.csv"),
        trend_fc=pd.read_csv(PROCESSED / "trend_forecast.csv", parse_dates=["week"]),
    )


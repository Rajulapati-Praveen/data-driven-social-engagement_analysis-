"""
Growth Visualization Dashboard (Module 6 / Deliverable 1)  -  run with:  streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import PROCESSED, REPORTS
from src import sentiment

st.set_page_config(page_title="Data-Driven Social Engagement", page_icon="", layout="wide")


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


try:
    D = load()
except FileNotFoundError:
    st.error("Results not found. Run `python run_pipeline.py` first, then reload this page.")
    st.stop()

posts = D["posts"]
st.title("The Data-Driven Social Engagement Initiative")
st.caption("Measuring relatability: from raw engagement to evidence-based content strategy")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
topics = st.sidebar.multiselect("Topics", sorted(posts["topic"].unique()), default=sorted(posts["topic"].unique()))
formats = st.sidebar.multiselect("Format", sorted(posts["format"].unique()), default=sorted(posts["format"].unique()))
dmin, dmax = posts["post_date"].min().date(), posts["post_date"].max().date()
date_range = st.sidebar.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
f = posts[posts["topic"].isin(topics) & posts["format"].isin(formats)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    f = f[(f["post_date"].dt.date >= date_range[0]) & (f["post_date"].dt.date <= date_range[1])]
if f.empty:
    st.warning("No posts match the filters.")
    st.stop()

tabs = st.tabs(["Overview", "Virality & Topics", "Sentiment", "A/B Tests", "Recommendations", "Trends", "Report"])

# ---------------- Overview ----------------
with tabs[0]:
    c = st.columns(5)
    c[0].metric("Posts", len(f))
    c[1].metric("Total views", f"{f['views'].sum():,}")
    c[2].metric("Followers gained", f"{f['followers_gained'].sum():,}")
    c[3].metric("Avg Viral Coefficient", f"{f['viral_coefficient'].mean():.2f}")
    c[4].metric("Avg Relatability", f"{f['relatability_score'].mean():.0%}")

    weekly = f.groupby("week").agg(followers_gained=("followers_gained", "sum"),
                                   viral_coefficient=("viral_coefficient", "mean")).reset_index()
    weekly["cumulative_followers"] = weekly["followers_gained"].cumsum()
    a, b = st.columns(2)
    a.plotly_chart(px.area(weekly, x="week", y="cumulative_followers", title="Cumulative follower growth"),
                   width="stretch")
    b.plotly_chart(px.line(weekly, x="week", y="viral_coefficient", markers=True,
                           title="Weekly average Viral Coefficient"), width="stretch")

# ---------------- Virality & topics ----------------
with tabs[1]:
    st.subheader("Which 'struggle topics' drive growth?")
    agg = f.groupby("topic").agg(mean_vc=("viral_coefficient", "mean"), followers=("followers_gained", "sum"),
                                 posts=("content_id", "count"), shares=("shares", "sum"), saves=("saves", "sum")).reset_index()
    agg["save_to_share"] = agg["saves"] / agg["shares"]
    a, b = st.columns(2)
    a.plotly_chart(px.bar(agg.sort_values("mean_vc"), x="mean_vc", y="topic", orientation="h",
                          title="Average Viral Coefficient by topic"), width="stretch")
    b.plotly_chart(px.scatter(agg, x="mean_vc", y="followers", size="posts", text="topic",
                              title="Virality vs followers gained (bubble = number of posts)"), width="stretch")
    st.plotly_chart(px.bar(agg.sort_values("save_to_share"), x="topic", y="save_to_share",
                           title="Save-to-Share ratio (higher = 'this is for me'; lower = 'send this to a friend')"),
                    width="stretch")
    st.plotly_chart(px.scatter(f, x="relatability_score", y="viral_coefficient", color="topic", trendline="ols",
                               trendline_scope="overall", title="Do relatable comments predict virality?"),
                    width="stretch")
    st.markdown("**Topic ranking with 95% bootstrap confidence intervals**")
    st.dataframe(D["ranking"].round(2), width="stretch", hide_index=True)

# ---------------- Sentiment ----------------
with tabs[2]:
    cm = D["comments"][D["comments"]["content_id"].isin(f["content_id"])]
    a, b = st.columns(2)
    dist = cm["ml_label"].value_counts().reset_index()
    dist.columns = ["label", "count"]
    a.plotly_chart(px.pie(dist, names="label", values="count", title="Comment tags"), width="stretch")
    by_topic = cm.merge(f[["content_id", "topic"]], on="content_id").groupby("topic")["ml_label"] \
        .apply(lambda s: (s == "Relatable").mean()).reset_index(name="relatable_share")
    b.plotly_chart(px.bar(by_topic.sort_values("relatable_share"), x="relatable_share", y="topic", orientation="h",
                          title="% comments tagged Relatable, by topic"), width="stretch")
    trig = cm[cm["triggers"].notna()]["triggers"].str.split(",").explode().value_counts().reset_index()
    trig.columns = ["linguistic trigger", "count"]
    st.plotly_chart(px.bar(trig, x="linguistic trigger", y="count", title="Which linguistic triggers appear most?"),
                    width="stretch")

    st.subheader("Try the NLP model")
    txt = st.text_input("Type a comment", "omg this is so me, I thought I was the only one 😭")
    if txt:
        try:
            model = sentiment.load_model()
        except Exception:
            model = None
        res = sentiment.tag_comment(txt, model)
        ml_part = (f"**ML tag:** {res['ml_label']} (confidence {res['ml_confidence']:.0%})  |  "
                   if "ml_label" in res else "")
        st.write(f"{ml_part}"
                 f"**Rule tag:** {res['rule_label']}  |  **Triggers:** {', '.join(res['triggers']) or 'none'}  |  "
                 f"**Polarity:** {res['polarity']}")

# ---------------- A/B ----------------
with tabs[3]:
    st.subheader("Statistical tests: what truly changes engagement?")
    metric = st.selectbox("Metric", ["viral_coefficient", "retention_rate", "engagement_rate"])
    ab = D["ab"][D["ab"]["metric"] == metric][["factor", "variants", "test", "p_value", "cohens_d",
                                              "effect_size", "best_variant", "verdict"]]
    st.dataframe(ab.round(4), width="stretch", hide_index=True)
    factor = st.selectbox("Visualise factor", ["format", "hook_type", "caption_style", "time_slot", "day_of_week"])
    st.plotly_chart(px.box(f, x=factor, y=metric, points="all", title=f"{metric} by {factor}"),
                    width="stretch")

# ---------------- Recommender ----------------
with tabs[4]:
    st.subheader("Recommended content plan for the coming week")
    r = D["recs"].copy()
    r["post_at"] = r["post_hour"].astype(int).astype(str) + ":00"
    st.dataframe(r[["topic", "format", "hook_type", "caption_style", "duration_sec", "post_at", "predicted_vc"]]
                 .round(2), width="stretch", hide_index=True)
    st.caption("Predicted by a Gradient Boosting model trained on your historical posts.")

# ---------------- Trends ----------------
with tabs[5]:
    st.subheader("Trend forecasting: rising 'relatable struggles'")
    st.dataframe(D["trend_sum"].round(1), width="stretch", hide_index=True)
    kw = st.selectbox("Keyword", D["trend_sum"]["keyword"])
    hist = D["trends"][D["trends"]["keyword"] == kw].assign(kind="actual")
    fc = D["trend_fc"][D["trend_fc"]["keyword"] == kw]
    st.plotly_chart(px.line(pd.concat([hist, fc]), x="week", y="interest", color="kind",
                            title=f"'{kw}': actual vs 4-week forecast"), width="stretch")

# ---------------- Report ----------------
with tabs[6]:
    rp = REPORTS / "strategy_report.md"
    st.markdown(rp.read_text(encoding="utf-8") if rp.exists() else "Run the pipeline to generate the report.")

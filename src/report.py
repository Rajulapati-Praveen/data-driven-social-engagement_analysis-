"""
STEP 8. Strategy Report (Deliverable 4) - auto-generated Markdown from the analysis results.
"""
import pandas as pd
from .config import PROCESSED, REPORTS


def build_report() -> str:
    posts = pd.read_csv(PROCESSED / "posts_scored.csv")
    ranking = pd.read_csv(PROCESSED / "topic_ranking.csv")
    ab = pd.read_csv(PROCESSED / "ab_test_results.csv")
    recs = pd.read_csv(PROCESSED / "weekly_recommendations.csv")
    trends = pd.read_csv(PROCESSED / "trend_summary.csv")

    top, bottom = ranking.iloc[0], ranking.iloc[-1]
    corr = posts[["relatability_score", "viral_coefficient"]].corr().iloc[0, 1]
    vc_ab = ab[(ab["metric"] == "viral_coefficient") & (ab["significant"])]

    L = []
    L.append("# Strategy Report: The Data-Driven Social Engagement Initiative\n")
    L.append("## 1. Executive summary")
    L.append(f"- Analysed **{len(posts)} posts** ({int(posts['views'].sum()):,} views, "
             f"{int(posts['followers_gained'].sum()):,} followers gained).")
    L.append(f"- **Most viral topic:** {top['topic']} (Viral Coefficient {top['mean_vc']:.2f}, "
             f"95% CI {top['ci_low']:.2f}-{top['ci_high']:.2f}). **Least viral:** {bottom['topic']} ({bottom['mean_vc']:.2f}).")
    strength = "strongly" if abs(corr) > 0.5 else "moderately" if abs(corr) > 0.3 else "weakly"
    L.append(f"- Share of comments tagged *Relatable* is {strength} correlated with virality (r = {corr:.2f}).")
    L.append(f"- {len(vc_ab)} content variables showed a statistically significant effect on virality.\n")

    L.append("## 2. Which topics drive the most connection?")
    L.append("| Rank | Topic | Posts | Viral Coefficient | Avg shares | Avg saves | Avg followers gained |")
    L.append("|---|---|---|---|---|---|---|")
    for i, r in ranking.iterrows():
        L.append(f"| {i+1} | {r['topic']} | {int(r['posts'])} | {r['mean_vc']:.2f} | {r['avg_shares']:.0f} | "
                 f"{r['avg_saves']:.0f} | {r['avg_followers_gained']:.0f} |")

    L.append("\n## 3. A/B testing findings (on Viral Coefficient)")
    if len(vc_ab):
        for _, r in vc_ab.iterrows():
            L.append(f"- **{r['factor']}**: best = **{r['best_variant']}** ({r['variants']}); p = {r['p_value']:.4f}, "
                     f"effect size: {r['effect_size'] if isinstance(r['effect_size'], str) else 'n/a (3+ groups)'}.")
    else:
        L.append("- No variable showed a statistically significant effect.")
    ns = ab[(ab["metric"] == "viral_coefficient") & (~ab["significant"])]["factor"].tolist()
    if ns:
        L.append(f"- No reliable difference found for: {', '.join(ns)}. Don't over-optimise these.")

    L.append("\n## 4. Recommended content plan for next week")
    L.append("| # | Topic | Format | Hook | Caption | Length (s) | Post at | Predicted VC |")
    L.append("|---|---|---|---|---|---|---|---|")
    for i, r in recs.iterrows():
        L.append(f"| {i+1} | {r['topic']} | {r['format']} | {r['hook_type']} | {r['caption_style']} | "
                 f"{int(r['duration_sec'])} | {int(r['post_hour'])}:00 | {r['predicted_vc']:.2f} |")

    L.append("\n## 5. Emerging 'relatable struggles' (trend forecast)")
    for _, r in trends.head(4).iterrows():
        L.append(f"- **{r['keyword']}** - {r['status']}: momentum {r['momentum_pct']:+.0f}%, "
                 f"forecast interest in 4 weeks = {r['forecast_4w']:.0f}/100.")

    L.append("\n## 6. Limitations & next steps")
    L.append("- Results come from observational data: effects of format/time may be confounded by topic. "
             "Run true A/B tests (same idea, two versions) to confirm.")
    L.append("- Replace the simulated dataset with real account data and re-run the pipeline.")
    L.append("- Re-train the sentiment model on ~500 hand-labelled real comments for best accuracy.")
    return "\n".join(L)


def main():
    text = build_report()
    (REPORTS / "strategy_report.md").write_text(text, encoding="utf-8")
    print("[report] wrote reports/strategy_report.md")


if __name__ == "__main__":
    main()

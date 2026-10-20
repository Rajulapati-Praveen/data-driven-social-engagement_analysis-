"""
STEP 3. Virality Prediction Engine (Module 2).

Viral Coefficient (VC) = weighted actions per 100 views
    weighted actions = 5*shares + 3*saves + 1.5*comments + 0.5*likes
Shares and saves count far more than likes because they signal "this is worth passing on / returning to".

We then
  (a) score every post,
  (b) rank topics by average VC with bootstrap 95% confidence intervals,
  (c) test (ANOVA / Kruskal-Wallis) whether topics really differ.
"""
import numpy as np
import pandas as pd
from scipy import stats
from .config import VIRAL_WEIGHTS, PROCESSED, RANDOM_SEED


def add_viral_coefficient(df: pd.DataFrame) -> pd.DataFrame:
    w = VIRAL_WEIGHTS
    df = df.copy()
    weighted = sum(df[k] * v for k, v in w.items())
    df["viral_coefficient"] = weighted / df["views"] * 100
    return df


def bootstrap_ci(x, n_boot=2000, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    means = [rng.choice(x, len(x), replace=True).mean() for _ in range(n_boot)]
    return np.percentile(means, [2.5, 97.5])


def topic_ranking(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for topic, g in df.groupby("topic"):
        lo, hi = bootstrap_ci(g["viral_coefficient"])
        rows.append(dict(topic=topic, posts=len(g), mean_vc=g["viral_coefficient"].mean(),
                         ci_low=lo, ci_high=hi, avg_shares=g["shares"].mean(), avg_saves=g["saves"].mean(),
                         avg_followers_gained=g["followers_gained"].mean(),
                         save_to_share=g["saves"].sum() / max(g["shares"].sum(), 1)))
    out = pd.DataFrame(rows).sort_values("mean_vc", ascending=False).reset_index(drop=True)
    return out


def topic_significance(df: pd.DataFrame) -> dict:
    groups = [g["viral_coefficient"].values for _, g in df.groupby("topic") if len(g) >= 2]
    if len(groups) < 2:
        return {"anova_F": float("nan"), "anova_p": float("nan"), "kruskal_H": float("nan"), "kruskal_p": float("nan")}
    f, p_anova = stats.f_oneway(*groups)
    h, p_kw = stats.kruskal(*groups)
    return {"anova_F": f, "anova_p": p_anova, "kruskal_H": h, "kruskal_p": p_kw}


def main():
    df = pd.read_csv(PROCESSED / "posts_clean.csv", parse_dates=["post_date"])
    df = add_viral_coefficient(df)
    df.to_csv(PROCESSED / "posts_scored.csv", index=False)
    ranking = topic_ranking(df)
    ranking.to_csv(PROCESSED / "topic_ranking.csv", index=False)
    sig = topic_significance(df)
    print("[virality] Topic ranking by Viral Coefficient:")
    print(ranking[["topic", "posts", "mean_vc", "ci_low", "ci_high"]].round(2).to_string(index=False))
    print(f"[virality] ANOVA p={sig['anova_p']:.2e}  Kruskal p={sig['kruskal_p']:.2e}")


if __name__ == "__main__":
    main()

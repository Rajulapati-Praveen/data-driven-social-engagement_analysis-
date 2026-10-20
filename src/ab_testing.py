"""
STEP 5. A/B Testing Framework (Module 4).

For every content variable we compare the Viral Coefficient between variants and report:
  - mean of each variant
  - Welch t-test p-value (2 groups) or ANOVA (3+ groups)
  - Mann-Whitney U / Kruskal-Wallis (non-parametric backup, robust to skewed data)
  - Cohen's d (effect size: is the difference big enough to matter?)
  - verdict at alpha = 0.05

NOTE: with historical (observational) data this is a "quasi-experiment".
For true A/B tests, post two versions of the same idea at matched times and feed them in here.
"""
import numpy as np
import pandas as pd
from scipy import stats
from .config import PROCESSED

ALPHA = 0.05
METRICS = ["viral_coefficient", "retention_rate", "engagement_rate"]


def cohens_d(a, b):
    na, nb = len(a), len(b)
    pooled = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1)) / (na + nb - 2))
    return (np.mean(a) - np.mean(b)) / pooled if pooled else 0.0


def effect_label(d):
    d = abs(d)
    return "large" if d >= 0.8 else "medium" if d >= 0.5 else "small" if d >= 0.2 else "negligible"


def compare(df, factor, metric):
    groups = {k: g[metric].dropna().values for k, g in df.groupby(factor)}
    groups = {k: v for k, v in groups.items() if len(v) >= 2}   # need at least 2 posts per variant
    names = list(groups)
    if len(names) < 2:
        return None   # nothing to compare (e.g. every post is 'Unlabelled')
    means = {k: float(np.mean(v)) for k, v in groups.items()}
    if len(names) == 2:
        a, b = groups[names[0]], groups[names[1]]
        t, p = stats.ttest_ind(a, b, equal_var=False)
        _, p_np = stats.mannwhitneyu(a, b, alternative="two-sided")
        d = cohens_d(a, b)
        winner = names[0] if means[names[0]] > means[names[1]] else names[1]
        test = "Welch t-test"
    else:
        _, p = stats.f_oneway(*groups.values())
        _, p_np = stats.kruskal(*groups.values())
        d = np.nan
        winner = max(means, key=means.get)
        test = "ANOVA"
    return dict(factor=factor, metric=metric, variants=" vs ".join(f"{k} ({means[k]:.3f})" for k in names),
                test=test, p_value=p, p_nonparametric=p_np, cohens_d=d,
                effect_size=effect_label(d) if not np.isnan(d) else "n/a",
                best_variant=winner, significant=bool(p < ALPHA and p_np < ALPHA))


def run_all(df: pd.DataFrame) -> pd.DataFrame:
    factors = ["format", "hook_type", "is_evening", "caption_style", "time_slot", "day_of_week"]
    rows = [r for r in (compare(df, f, m) for f in factors for m in METRICS) if r is not None]
    if not rows:
        print("[ab_testing] Not enough labelled variants to compare. Fill hook_type / caption_style in posts_raw.csv.")
        return pd.DataFrame(columns=["factor", "metric", "variants", "test", "p_value", "p_nonparametric",
                                     "cohens_d", "effect_size", "best_variant", "significant", "verdict"])
    out = pd.DataFrame(rows)
    out["verdict"] = np.where(out["significant"], "Statistically significant", "No significant difference")
    return out.sort_values(["significant", "p_value"], ascending=[False, True]).reset_index(drop=True)


def main():
    df = pd.read_csv(PROCESSED / "posts_scored.csv")
    res = run_all(df)
    res.to_csv(PROCESSED / "ab_test_results.csv", index=False)
    if res.empty:
        return
    show = res[res["metric"] == "viral_coefficient"][["factor", "variants", "p_value", "cohens_d", "verdict"]]
    print("[ab_testing] Results on Viral Coefficient:")
    print(show.round(4).to_string(index=False))


if __name__ == "__main__":
    main()

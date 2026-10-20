"""
STEP 6. Engagement Optimization Recommender (Module 5).

Prescriptive analytics: train a Gradient Boosting model that predicts a post's Viral Coefficient
from its choices (topic, format, hook, caption style, length, posting time).  Then we score every
possible combination of choices, and recommend the best ones for the coming week.
"""
import itertools
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from .config import PROCESSED, MODELS, RANDOM_SEED

CAT = ["topic", "format", "hook_type", "caption_style"]
NUM = ["duration_sec", "post_hour"]


def build_model():
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CAT)], remainder="passthrough")
    return Pipeline([("pre", pre),
                     ("gbr", GradientBoostingRegressor(n_estimators=250, max_depth=3, learning_rate=0.05,
                                                       subsample=0.8, random_state=RANDOM_SEED))])


def train(df):
    X, y = df[CAT + NUM], df["viral_coefficient"]
    model = build_model()
    r2 = cross_val_score(model, X, y, cv=min(5, max(2, len(df) // 3)), scoring="r2")
    model.fit(X, y)
    return model, r2


def recommend(model, df, top_n=5, one_per_topic=True):
    """Score all combinations and return the top strategies."""
    grid = pd.DataFrame(list(itertools.product(
        sorted(df["topic"].unique()), ["Short", "Long"], ["Visual", "Text"],
        ["Question", "Story", "Listicle"], [18, 25, 60, 90], [19, 20, 21])),
        columns=CAT[:1] + CAT[1:3] + ["caption_style", "duration_sec", "post_hour"])
    # keep logically consistent combos (Short ~ <35 sec, Long ~ >45 sec)
    grid = grid[((grid["format"] == "Short") & (grid["duration_sec"] < 35)) |
                ((grid["format"] == "Long") & (grid["duration_sec"] > 45))].copy()
    grid["predicted_vc"] = model.predict(grid[CAT + NUM])
    grid = grid.sort_values("predicted_vc", ascending=False)
    if one_per_topic:
        grid = grid.drop_duplicates("topic")
    return grid.head(top_n).reset_index(drop=True)


def main():
    df = pd.read_csv(PROCESSED / "posts_scored.csv")
    model, r2 = train(df)
    joblib.dump(model, MODELS / "recommender_model.joblib")
    recs = recommend(model, df)
    recs.to_csv(PROCESSED / "weekly_recommendations.csv", index=False)
    print(f"[recommender] 5-fold CV R^2 = {r2.mean():.2f} (+/- {r2.std():.2f})")
    print("[recommender] Recommended strategy for next week:")
    print(recs.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

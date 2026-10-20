"""
STEP 4. Audience Sentiment Analyzer (Module 3) + NLP Sentiment Model (Deliverable 3).

Two taggers that label each comment "Relatable" or "Neutral":
  1. RULE-BASED  - looks for linguistic triggers ("me too", "so me", "needed this", "I feel"...)
  2. ML MODEL    - TF-IDF + Logistic Regression that learns the pattern from labelled examples

We also add TextBlob polarity (positive/negative tone) as an extra signal.
Then comments are aggregated per post into a "Relatability Score" (% of comments tagged Relatable).
"""
import re
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from .config import PROCESSED, MODELS, RANDOM_SEED

try:
    from textblob import TextBlob
except Exception:  # TextBlob optional
    TextBlob = None

# Linguistic triggers that signal "Problem Awareness" / feeling understood
TRIGGER_PATTERNS = {
    "identification": r"\b(so me|literally me|that'?s me|described me|my life|i relate|relate to|relatable|same here|me too|same)\b",
    "validation": r"\b(finally someone|someone gets it|gets it|needed this|needed to hear|thank you for saying|so true|exactly how i feel)\b",
    "first_person_feeling": r"\b(i feel|i felt|i thought i was|i'?ve been there|felt this|feel this|only one)\b",
    "sharing_intent": r"\b(sending this|saving this|sharing this|tagging|send this to)\b",
}
_COMPILED = {k: re.compile(v) for k, v in TRIGGER_PATTERNS.items()}


def rule_based_tag(text: str):
    """Return (label, trigger_count, triggers_found)."""
    text = str(text).lower()
    found = [name for name, rx in _COMPILED.items() if rx.search(text)]
    return ("Relatable" if found else "Neutral"), len(found), found


def polarity(text: str) -> float:
    return float(TextBlob(str(text)).sentiment.polarity) if TextBlob else 0.0


def train_model(comments: pd.DataFrame):
    """Train on the labelled comments. In real life you hand-label ~300-500 comments."""
    X, y = comments["clean_text"], comments["true_label"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y)
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    report = classification_report(y_te, pred, digits=3)
    rule_pred = X_te.map(lambda t: rule_based_tag(t)[0])
    metrics = {"ml_accuracy": accuracy_score(y_te, pred), "rule_accuracy": accuracy_score(y_te, rule_pred)}
    return model, report, metrics


def load_model():
    return joblib.load(MODELS / "relatability_model.joblib")


def tag_comment(text: str, model=None) -> dict:
    """Convenience function used by the dashboard's live demo."""
    from .clean_data import clean_text
    t = clean_text(text)
    label, n, found = rule_based_tag(t)
    out = {"rule_label": label, "triggers": found, "polarity": round(polarity(t), 3)}
    if model is not None:
        out["ml_label"] = model.predict([t])[0]
        out["ml_confidence"] = float(max(model.predict_proba([t])[0]))
    return out


def main():
    comments = pd.read_csv(PROCESSED / "comments_clean.csv")
    posts = pd.read_csv(PROCESSED / "posts_scored.csv")

    tags = comments["clean_text"].map(rule_based_tag)
    comments["rule_label"] = tags.map(lambda x: x[0])
    comments["trigger_count"] = tags.map(lambda x: x[1])
    comments["triggers"] = tags.map(lambda x: ",".join(x[2]))

    # Real comments usually have no hand-made labels. Then the rule-based tags are used as
    # "weak labels" to train the ML model (it learns the rules + related wording).
    has_labels = "true_label" in comments.columns and comments["true_label"].notna().all()
    if not has_labels:
        print("[sentiment] NOTE: no hand-labelled 'true_label' column found - using rule-based tags as training labels. "
              "For better accuracy, hand-label 300-500 comments as Relatable/Neutral in comments_raw.csv.")
        comments["true_label"] = comments["rule_label"]

    if comments["true_label"].value_counts().min() >= 4 and comments["true_label"].nunique() == 2:
        model, report, metrics = train_model(comments)
        joblib.dump(model, MODELS / "relatability_model.joblib")
        print("[sentiment] ML model performance on held-out comments:\n" + report)
        print(f"[sentiment] accuracy  ML={metrics['ml_accuracy']:.3f}  rule-based={metrics['rule_accuracy']:.3f}")
        comments["ml_label"] = model.predict(comments["clean_text"])
    else:
        print("[sentiment] Too few comments of one type to train the ML model - using rule-based tags only.")
        (MODELS / "relatability_model.joblib").unlink(missing_ok=True)
        comments["ml_label"] = comments["rule_label"]
    comments["polarity"] = comments["clean_text"].map(polarity)
    comments.to_csv(PROCESSED / "comments_tagged.csv", index=False)

    per_post = (comments.groupby("content_id")
                .agg(n_comments=("comment_id", "count"),
                     relatability_score=("ml_label", lambda s: (s == "Relatable").mean()),
                     avg_polarity=("polarity", "mean")).reset_index())
    posts = posts.drop(columns=[c for c in ["relatability_score", "avg_polarity", "n_comments"] if c in posts.columns])
    posts = posts.merge(per_post, on="content_id", how="left")
    posts.to_csv(PROCESSED / "posts_scored.csv", index=False)
    corr = posts[["relatability_score", "viral_coefficient"]].corr().iloc[0, 1]
    print(f"[sentiment] correlation(relatability score, viral coefficient) = {corr:.2f}")


if __name__ == "__main__":
    main()

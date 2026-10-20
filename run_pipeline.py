"""Run the entire analysis pipeline with one command:   python run_pipeline.py

Use `python run_pipeline.py --real` to skip the simulated-data step once you've put your own
posts_raw.csv / comments_raw.csv / trends_raw.csv into data/raw/ (see README).
"""
import sys
from src import generate_data, clean_data, virality, sentiment, ab_testing, recommender, trends, report

steps = [
    ("1. Generate practice data", generate_data.main),
    ("2. Clean data + load database", clean_data.main),
    ("3. Virality engine", virality.main),
    ("4. NLP sentiment model", sentiment.main),
    ("5. A/B testing", ab_testing.main),
    ("6. Recommender", recommender.main),
    ("7. Trend forecasting", trends.main),
    ("8. Strategy report", report.main),
]

if __name__ == "__main__":
    if "--real" in sys.argv:
        steps = steps[1:]
    for name, fn in steps:
        print(f"\n===== {name} =====")
        fn()
    print("\nDone! Launch the dashboard with:  streamlit run app.py")

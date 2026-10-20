"""
STEP 7. Trend Forecasting Module (Module 7).

For each external keyword/hashtag we
  - fit a linear trend on the most recent 12 weeks (slope in points/week, with a p-value),
  - compute momentum = (avg of last 4 weeks) / (avg of previous 8 weeks) - 1,
  - forecast the next 4 weeks using Holt's exponential smoothing (level + trend),
  - label it Rising / Stable / Declining, flagging "Emerging" when momentum is high but interest is still lowish.
Real data: export Google Trends CSVs (trends.google.com) or use the pytrends package, then
save in the same format as data/raw/trends_raw.csv  (week, keyword, interest).
"""
import numpy as np
import pandas as pd
from scipy import stats
from .config import PROCESSED


def holt_forecast(y, alpha=0.5, beta=0.3, horizon=4):
    level, trend = y[0], y[1] - y[0]
    for v in y[1:]:
        prev = level
        level = alpha * v + (1 - alpha) * (level + trend)
        trend = beta * (level - prev) + (1 - beta) * trend
    return np.array([level + (h + 1) * trend for h in range(horizon)])


def analyse(trends: pd.DataFrame, window=12):
    rows, fc_rows = [], []
    for kw, g in trends.sort_values("week").groupby("keyword"):
        y = g["interest"].values
        recent = y[-window:]
        slope, _, _, p, _ = stats.linregress(np.arange(len(recent)), recent)
        momentum = recent[-4:].mean() / recent[:-4].mean() - 1
        fc = np.clip(holt_forecast(y), 0, 100)
        status = "Rising" if slope > 0.5 and p < 0.05 else "Declining" if slope < -0.5 and p < 0.05 else "Stable"
        if status == "Rising" and momentum > 0.15 and y[-1] < 70:
            status = "Rising (Emerging)"
        rows.append(dict(keyword=kw, current_interest=y[-1], slope_per_week=slope, slope_p=p,
                         momentum_pct=momentum * 100, forecast_4w=fc[-1], status=status))
        last = g["week"].max()
        for h, v in enumerate(fc, 1):
            fc_rows.append(dict(keyword=kw, week=last + pd.Timedelta(weeks=h), interest=v, kind="forecast"))
    summary = pd.DataFrame(rows).sort_values("momentum_pct", ascending=False).reset_index(drop=True)
    return summary, pd.DataFrame(fc_rows)


def main():
    trends = pd.read_csv(PROCESSED / "trends_clean.csv", parse_dates=["week"])
    summary, fc = analyse(trends)
    summary.to_csv(PROCESSED / "trend_summary.csv", index=False)
    fc.to_csv(PROCESSED / "trend_forecast.csv", index=False)
    print("[trends] Keyword momentum:")
    print(summary[["keyword", "current_interest", "momentum_pct", "forecast_4w", "status"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()

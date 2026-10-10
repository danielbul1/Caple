"""Walk-forward test: does picking past days by day-of-month beat just using all of them?

For every day after a warm-up, each method builds its sample only from earlier days,
the way quantistat.py would have that morning, and is scored against what happened.
The bias is taken as known (the day's real direction), the same for every method, so
this measures the charts, not the bias call.

- time_score: share of the same-bias sample whose HOD/LOD hour matched the day's real
  HOD/LOD hour (average of the two). Higher is better; guessing uniformly gives ~4%.
- price_error: points between the sample's median distance from the open (HOD side
  if bullish, LOD side if bearish) and the real one. Lower is better.

Run: python backtest.py
"""

import pandas as pd

from app import fetch_candles, today_market
from quantistat import daily_stats

SAMPLERS = {
    "same day of month": lambda d: lambda past: past.day == d.day,
    "same weekday": lambda d: lambda past: past.weekday() == d.weekday(),
    "all days": lambda d: lambda past: True,
}


def backtest(stats: pd.DataFrame, warmup: int = 120) -> pd.DataFrame:
    rows = []
    for i in range(warmup, len(stats)):
        day, history = stats.iloc[i], stats.iloc[:i]
        side = "high" if day.bullish else "low"
        samples = {name: history[history.index.map(match(stats.index[i]))] for name, match in SAMPLERS.items()}
        if any((s.bullish == day.bullish).sum() == 0 for s in samples.values()):
            continue  # score every method on the same days
        for name, sample in samples.items():
            same_bias = sample[sample.bullish == day.bullish]
            time_score = ((same_bias.hod_hour == day.hod_hour).mean() + (same_bias.lod_hour == day.lod_hour).mean()) / 2
            predicted = (sample[side] - sample.open).median()
            rows.append({"day": stats.index[i], "method": name, "time_score": time_score,
                         "price_error": abs(predicted - (day[side] - day.open))})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    result = backtest(daily_stats(fetch_candles(today_market())))
    print(f"{result.day.nunique()} test days, {result.day.min()} .. {result.day.max()}\n")
    print(result.groupby("method")[["time_score", "price_error"]].mean().round(3).to_string())
    wide = result.pivot(index="day", columns="method")
    print("\nVs all days (mean difference ± 2 standard errors):")
    for name in ("same day of month", "same weekday"):
        for col in ("time_score", "price_error"):
            diff = wide[col][name] - wide[col]["all days"]
            print(f"  {name:18} {col:12} {diff.mean():+.3f} ± {2 * diff.sem():.3f}")

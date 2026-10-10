"""Walk-forward test: does picking past days by day-of-month beat just using all of them?

For every day after a warm-up, each method builds its sample only from earlier days,
the way quantistat.py would have that morning, and is scored against what happened.
The bias is taken as known (the day's real direction), the same for every method, so
this measures the charts, not the bias call.

- time_score: share of the same-bias sample whose HOD/LOD hour matched the day's real
  HOD/LOD hour (average of the two). Higher is better; guessing uniformly gives ~4%.
- price_error: points between the same-bias sample's median distance from the open
  (HOD side if bullish, LOD side if bearish) and the real one. Lower is better.
- reached_75/50/25: did the day reach the level quantistat says 75%/50%/25% of days
  reach? Honest levels hit about that often.

Run: python backtest.py
"""

import pandas as pd

from quantistat import daily_stats, load_candles, reach_levels

SAMPLERS = {
    "same day of month": lambda d: lambda past: past.day == d.day,
    "same weekday": lambda d: lambda past: past.weekday() == d.weekday(),
    "all days": lambda d: lambda past: True,
}


def backtest(stats: pd.DataFrame, warmup: int = 120) -> pd.DataFrame:
    rows = []
    for i in range(warmup, len(stats)):
        day, history = stats.iloc[i], stats.iloc[:i]
        side = "HOD" if day.bullish else "LOD"
        actual = (day.high if day.bullish else day.low) - day.open
        samples = {name: history[history.index.map(match(stats.index[i]))] for name, match in SAMPLERS.items()}
        if any((s.bullish == day.bullish).sum() == 0 for s in samples.values()):
            continue  # score every method on the same days
        for name, sample in samples.items():
            same_bias = sample[sample.bullish == day.bullish]
            time_score = ((same_bias.hod_hour == day.hod_hour).mean() + (same_bias.lod_hour == day.lod_hour).mean()) / 2
            levels = reach_levels(same_bias, day.r5)[side]
            reached = [actual >= lvl if day.bullish else actual <= lvl for lvl in levels]
            rows.append({"day": stats.index[i], "method": name, "time_score": time_score,
                         "price_error": abs(levels[1] - actual),
                         **dict(zip(["reached_75", "reached_50", "reached_25"], reached))})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    result = backtest(daily_stats(load_candles()))
    print(f"{result.day.nunique()} test days, {result.day.min()} .. {result.day.max()}\n")
    print(result.groupby("method").mean(numeric_only=True).round(3).to_string())
    wide = result.pivot(index="day", columns="method")
    print("\nVs all days (mean difference ± 2 standard errors):")
    for name in ("same day of month", "same weekday"):
        for col in ("time_score", "price_error"):
            diff = wide[col][name] - wide[col]["all days"]
            print(f"  {name:18} {col:12} {diff.mean():+.3f} ± {2 * diff.sem():.3f}")

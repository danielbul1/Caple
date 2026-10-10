"""Every trading day: what did levels.py say, and was it right?

For a finished calendar day (00:00-23:00 New York) it replays levels.py's forecast
before the open and after the 2/5/9/12/15:00 candles from earlier days only, scores it
against the day and appends the rows to journal.csv (a re-run replaces that day):

- *_call_right: the more likely side came true (HOD said "already in" at >= 50% and it
  was, or said "still to come" and it was)
- *_75/50/25: on days that went further, was the level reached (honest: ~75/50/25%)
- *_miss, *_pinball: points off, as in `levels.py backtest`

Then prints the day and the running record of every day in the journal.

Run: python journal.py [DATE ...]   (default: yesterday, New York time; meant for just
     after midnight New York, when the calendar day is complete)
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from app import today_market
from levels import through_hour, use_implied, walk_forward
from quantistat import daily_stats, load_candles

JOURNAL = Path(__file__).with_name("journal.csv")


def add_verdicts(rows: pd.DataFrame) -> pd.DataFrame:
    return rows.assign(**{f"{s}_call_right": (rows[f"{s}_done_pred"] >= 0.5) == (rows[f"{s}_done_real"] == 1)
                          for s in ("HOD", "LOD")})


def score_day(candles: pd.DataFrame, target: date) -> pd.DataFrame:
    """Empty if the day is not scored (no 00:00 open, expiry week or contract roll)."""
    stats = daily_stats(candles)
    use_implied(stats)
    stats = stats.dropna()
    stats = stats[stats.index <= target]
    if len(stats) == 0 or stats.index[-1] != target:
        return pd.DataFrame()
    return add_verdicts(walk_forward(stats, *through_hour(candles), warmup=len(stats) - 1))


def append(path: Path, rows: pd.DataFrame) -> None:
    old = pd.read_csv(path, parse_dates=["day"]) if path.exists() else pd.DataFrame(columns=rows.columns)
    old.day = pd.to_datetime(old.day).dt.date
    keep = old[~old.day.isin(set(rows.day))]
    pd.concat([keep, rows]).sort_values("day", kind="stable").to_csv(path, index=False)


if __name__ == "__main__":
    days = [date.fromisoformat(d) for d in sys.argv[1:]] or [today_market() - timedelta(days=1)]
    candles = load_candles()
    for day in days:
        rows = score_day(candles, day)
        if rows.empty:
            print(f"{day}: not scored (weekend/holiday, expiry week, contract roll or no 00:00 open)")
            continue
        append(JOURNAL, rows)
        print(f"{day}:")
        for _, r in rows.iterrows():
            print(f"  {r.hour:>5}  HOD in {r.HOD_done_pred:4.0%} -> {'right' if r.HOD_call_right else 'WRONG'}, "
                  f"off {r.HOD_miss:5.1f} pts | LOD in {r.LOD_done_pred:4.0%} -> "
                  f"{'right' if r.LOD_call_right else 'WRONG'}, off {r.LOD_miss:5.1f} pts")
    record = pd.read_csv(JOURNAL) if JOURNAL.exists() else pd.DataFrame()
    if len(record):
        print(f"\nJournal: {record.day.nunique()} days, {record.day.min()} .. {record.day.max()}")
        print("calls right, levels reached (honest ~0.75/0.5/0.25) and points off, by hour:")
        cols = ["HOD_call_right", "LOD_call_right", "HOD_75", "HOD_50", "HOD_25", "LOD_75", "LOD_50", "LOD_25",
                "HOD_miss", "LOD_miss"]
        print(record.groupby("hour", sort=False)[cols].mean().round(2).to_string())

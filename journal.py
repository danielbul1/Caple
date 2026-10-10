"""Every trading day: what did levels.py say, and was it right?

For a finished calendar day (00:00-23:00 New York) it replays levels.py's forecast
before the open and after the 2/5/9/12/15:00 candles from earlier days only, scores it
against the day and appends the rows to journal.csv (a re-run replaces that day):

- *_call_right: the more likely side came true (HOD said "already in" at >= 50% and it
  was, or said "still to come" and it was)
- *_75/50/25: on days that went further, was the level reached (honest: ~75/50/25%)
- *_in_band: on those days, did the HOD/LOD land between the 75% and 25% levels (honest: ~50%)
- *_miss, *_pinball: points off, as in `levels.py backtest`

Then prints the day and the running record of every day in the journal.

Run: python journal.py [DATE or FROM..TO ...]   (default: yesterday, New York time; meant for just
     after midnight New York, when the calendar day is complete)
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from app import today_market
from levels import through_hour, walk_forward
from quantistat import daily_stats, load_candles

JOURNAL = Path(__file__).with_name("journal.csv")


def add_verdicts(rows: pd.DataFrame) -> pd.DataFrame:
    return rows.assign(**{f"{s}_call_right": (rows[f"{s}_done_pred"] >= 0.5) == (rows[f"{s}_done_real"] == 1)
                          for s in ("HOD", "LOD")},
                       **{f"{s}_in_band": ((rows[f"{s}_75"] == 1) & (rows[f"{s}_25"] == 0)).astype(float).where(rows[f"{s}_75"].notna())
                          for s in ("HOD", "LOD")})


def score_days(candles: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Every scored day from start to end, each from earlier days only; empty if none is scored
    (no 00:00 open, expiry week or contract roll)."""
    stats = daily_stats(candles)
    stats = stats.dropna()
    stats = stats[stats.index <= end]
    first = int((stats.index < start).sum())
    if first == len(stats):
        return pd.DataFrame()
    return add_verdicts(walk_forward(stats, *through_hour(candles), warmup=first))


def append(path: Path, rows: pd.DataFrame) -> None:
    old = pd.read_csv(path, parse_dates=["day"]) if path.exists() else pd.DataFrame(columns=rows.columns)
    old.day = pd.to_datetime(old.day).dt.date
    keep = old[~old.day.isin(set(rows.day))]
    pd.concat([keep, rows]).sort_values("day", kind="stable").to_csv(path, index=False)


if __name__ == "__main__":
    yesterday = (today_market() - timedelta(days=1)).isoformat()
    candles = load_candles()
    for arg in sys.argv[1:] or [yesterday]:
        start, end = (date.fromisoformat(d) for d in (arg.split("..") if ".." in arg else [arg, arg]))
        rows = score_days(candles, start, min(end, date.fromisoformat(yesterday)))  # today isn't finished
        if rows.empty:
            print(f"{arg}: not scored (weekend/holiday, expiry week, contract roll or no 00:00 open)")
            continue
        append(JOURNAL, rows)
        if start != end:
            print(f"{arg}: {rows.day.nunique()} days scored")
            continue
        print(f"{arg}:")
        for _, r in rows.iterrows():
            print(f"  {r.hour:>5}  HOD in {r.HOD_done_pred:4.0%} -> {'right' if r.HOD_call_right else 'WRONG'}, "
                  f"off {r.HOD_miss:5.1f} pts | LOD in {r.LOD_done_pred:4.0%} -> "
                  f"{'right' if r.LOD_call_right else 'WRONG'}, off {r.LOD_miss:5.1f} pts")
    record = pd.read_csv(JOURNAL) if JOURNAL.exists() else pd.DataFrame()
    if len(record):
        print(f"\nJournal: {record.day.nunique()} days, {record.day.min()} .. {record.day.max()}")
        print("calls right, levels reached (honest ~0.75/0.5/0.25) and points off, by hour:")
        cols = ["HOD_call_right", "LOD_call_right", "HOD_75", "HOD_50", "HOD_25", "LOD_75", "LOD_50", "LOD_25",
                "HOD_in_band", "LOD_in_band", "HOD_miss", "LOD_miss"]
        print(record.groupby("hour", sort=False)[cols].mean().round(2).to_string())

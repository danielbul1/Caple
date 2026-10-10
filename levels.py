"""Where will today's high (HOD) and low (LOD) be? No bias needed.

Before the open only the open is known; after each hourly candle the day's high
and low so far are known too. For every past day we measure how much further the
high still rose and the low still fell after that point, in units of that day's
prior 5-day average range (so 2016 and 2026 compare), using only past days where
price at that hour sat in the same half of the range so far as today (cuts the miss
~10% at 9:00). Today's levels are the high and low so far plus those extras times
today's 5-day range:

- done: share of past days whose HOD (or LOD) was already in at this point
- levels: if it goes further, the prices it reached on 75% / 50% / 25% of the past
  days that did go further (levels over all days would collapse onto the current
  high/low once most days are done, and be "reached" trivially)

Run: python levels.py [DATE] [HOUR]   (HOUR = after that hour's candle, "open" for the
     pre-open view; omit for the latest candle of DATE)
     python levels.py backtest        (walk-forward calibration on all the data)
"""

import os
import sys
from datetime import date

import numpy as np
import pandas as pd

import lse_source
from quantistat import REACH, daily_stats, load_candles, recent_range, today_market

CHECKPOINTS = [None, 2, 5, 9, 12, 15]  # None = before the open
QUANTILES = [0.25, 0.5, 0.75]
# Day range / prior 5-day average on event days vs 1.04 on ordinary days (2016-2026).
# Tried and rejected, each scored with pinball loss on 2017-2021 and 2022+: matching the
# share of a normal range already used (no gain), and forecasting FOMC/CPI days from past
# FOMC/CPI days only (better on 2022+, worse on 2017-2021), so events only get a warning.
EVENT_SIZE = {"FOMC": 1.3, "CPI": 1.2}


def through_hour(candles: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Running high, running low and last close of each calendar day after each hour
    (rows: days, columns: 0-23)."""
    keys = [candles.index.date, candles.index.hour]
    by_hour = lambda s, f: getattr(s.groupby(keys), f)().unstack().reindex(columns=range(24))
    return (by_hour(candles.High, "max").cummax(axis=1).ffill(axis=1),
            by_hour(candles.Low, "min").cummin(axis=1).ffill(axis=1),
            by_hour(candles.Close, "last").ffill(axis=1))


def upper_half(hi: pd.DataFrame, lo: pd.DataFrame, close: pd.DataFrame, hour: int) -> pd.Series:
    """Is price after `hour` in the upper half of the day's range so far?"""
    return close[hour] > (hi[hour] + lo[hour]) / 2


def pinball(actual: float, past: np.ndarray, now: float, sign: int, today_range: float) -> float:
    """Quantile (pinball) loss of the 25/50/75% levels over all past days: one proper score
    for the whole forecast, lower is better."""
    y = sign * (actual - now) / today_range
    return sum(max(q * (y - x), (q - 1) * (y - x)) for q, x in zip(QUANTILES, np.quantile(past, QUANTILES))) * today_range


def extras(stats: pd.DataFrame, hi: pd.DataFrame, lo: pd.DataFrame, hour: int | None) -> pd.DataFrame:
    """How far the HOD/LOD still went beyond the high/low known at `hour`, in 5-day ranges."""
    hi_now = stats.open if hour is None else hi[hour].reindex(stats.index)
    lo_now = stats.open if hour is None else lo[hour].reindex(stats.index)
    return pd.DataFrame({"up": (stats.high - hi_now) / stats.r5, "down": (lo_now - stats.low) / stats.r5})


def odds(extra: np.ndarray, now: float, sign: int, today_range: float) -> tuple[float, list[float]]:
    """(share already done, levels reached on 75/50/25% of the days that went further)."""
    more = extra[extra > 1e-9]
    if len(more) == 0:
        return 1.0, [np.nan] * len(REACH)
    return 1 - len(more) / len(extra), [now + sign * np.quantile(more, 1 - p) * today_range for p in REACH]


def forecast(ex: pd.DataFrame, high_so_far: float, low_so_far: float, today_range: float) -> dict:
    ex = ex.dropna()
    return {side: dict(zip(["done", "levels"], odds(ex[col].to_numpy(), now, sign, today_range)))
            for side, col, now, sign in [("HOD", "up", high_so_far, 1), ("LOD", "down", low_so_far, -1)]}


def walk_forward(stats: pd.DataFrame, hi: pd.DataFrame, lo: pd.DataFrame, close: pd.DataFrame,
                 warmup: int = 250) -> pd.DataFrame:
    """Each day forecast only from earlier days; did the HOD/LOD reach each level?"""
    rows = []
    for hour in CHECKPOINTS:
        ex = extras(stats, hi, lo, hour).to_numpy()
        hi_now = (stats.open if hour is None else hi[hour].reindex(stats.index)).to_numpy()
        lo_now = (stats.open if hour is None else lo[hour].reindex(stats.index)).to_numpy()
        upper = (np.zeros(len(stats), bool) if hour is None
                 else upper_half(hi, lo, close, hour).reindex(stats.index).to_numpy(bool))
        for i in range(warmup, len(stats)):
            past = ex[:i][~np.isnan(ex[:i]).any(axis=1) & (upper[:i] == upper[i])]
            day, r = stats.iloc[i], stats.r5.iloc[i]
            row = {"hour": "open" if hour is None else f"{hour}:00", "day": stats.index[i]}
            for side, col, now, sign, actual in [("HOD", 0, hi_now[i], 1, day.high), ("LOD", 1, lo_now[i], -1, day.low)]:
                done, lvls = odds(past[:, col], now, sign, r)
                went_further = sign * (actual - now) > 1e-9
                row |= {f"{side}_done_pred": done, f"{side}_done_real": float(not went_further),
                        **{f"{side}_{int(p * 100)}": float(sign * (actual - lvl) >= 0) if went_further and not np.isnan(lvl) else np.nan
                           for p, lvl in zip(REACH, lvls)},
                        f"{side}_miss": abs(actual - (now + sign * np.quantile(past[:, col], 0.5) * r)),
                        f"{side}_pinball": pinball(actual, past[:, col], now, sign, r)}
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    candles = load_candles()
    stats = daily_stats(candles)
    hi, lo, close = through_hour(candles)
    if sys.argv[1:2] == ["backtest"]:
        result = walk_forward(stats.dropna(), hi, lo, close)
        print(f"{result.day.nunique()} days, {result.day.min()} .. {result.day.max()}")
        print("*_done_pred vs *_done_real: forecast vs real share of days already done at that hour;")
        print("HOD_75 etc.: on days that went further, share reaching the '75%' level (honest: ~0.75);")
        print("*_miss: average points between the overall median forecast and the real HOD/LOD\n")
        print(result.groupby("hour", sort=False).mean(numeric_only=True).round(3).to_string())
        sys.exit()
    try:
        events = lse_source.events() if os.environ.get("LSE_API_KEY") else {}
    except OSError as e:  # the calendar only adds a warning; never block the forecast
        print(f"(event calendar unavailable: {e})")
        events = {}
    target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else today_market()
    day = candles[candles.index.date == target]
    hour = (day.index[-1].hour if len(day) else None) if len(sys.argv) < 3 else (
        None if sys.argv[2] == "open" else int(sys.argv[2]))
    if len(day) == 0 or day.index[0].hour != 0:
        sys.exit(f"No 00:00 candle for {target} yet: run after midnight New York time.")
    if hour is not None and hour > day.index[-1].hour:
        sys.exit(f"The {hour}:00 candle of {target} is not in yet (latest {day.index[-1].hour}:00).")
    history = stats[[d < target for d in stats.index]]
    if hour is not None:
        upper = upper_half(hi, lo, close, hour)
        history = history[upper.reindex(history.index) == upper[target]]
    today_range = recent_range(stats, target)
    open_price = day.Open.iloc[0]
    hod_now = open_price if hour is None else hi.loc[target, hour]
    lod_now = open_price if hour is None else lo.loc[target, hour]
    f = forecast(extras(history, hi, lo, hour), hod_now, lod_now, today_range)
    when = "before the open" if hour is None else f"after the {hour}:00 candle: high {hod_now:.2f}, low {lod_now:.2f}"
    kind = f"{events[target]} day, " if target in events else ""
    print(f"{target} {kind}open {open_price:.2f}, 5-day range {today_range:.1f}, {when}  ({len(history)} similar past days)")
    for side in ("HOD", "LOD"):
        lv = " / ".join(f"{x:.2f}" for x in f[side]["levels"])
        print(f"  {side}: already in on {f[side]['done']:.0%} of similar days; "
              f"if it goes further: {lv} (reached on 75% / 50% / 25% of those)")
    if target in events:
        print(f"  Warning: on past {events[target]} days the range ran ~{EVENT_SIZE[events[target]]}x normal and these "
              "levels were reached more often than stated (the 14:00 FOMC decision often sets the HOD/LOD late). "
              "Treat them as too tight. (Matching past event days instead did not hold up out of sample.)")
    if target < today_market():
        print(f"  actual: HOD {day.High.max():.2f} at {day.High.idxmax().hour}:00, "
              f"LOD {day.Low.min():.2f} at {day.Low.idxmin().hour}:00")

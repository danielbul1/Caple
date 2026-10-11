"""Where will today's high (HOD) and low (LOD) be? No bias needed.

Before the open only the open is known; after each hourly candle the day's high
and low so far are known too. For every past day we measure how much further the
high still rose and the low still fell after that point, in units of that day's
yardstick: its expected range from earlier days' hourly volatility (so calm and wild days
compare; see use_yardstick). Similar past days get the weight:
half on the days where price at that hour sat in the same fifth of the range so far as today
(halves cut the miss ~10% at 9:00; fifths, picked on 2018-2021, cut the pinball loss another
~4% at 9:00 and 12:00 on 2022-2026, paired t -4.6 and -5.0, and changed nothing before 5:00),
half on the K_NEAREST days closest in distance from the high and low so far (k-NN analogs;
all of it on the k-NN days if no past day shares today's fifth). Walk-forward vs the fifths
alone it cut the log loss of "already in" at every checkpoint from 2:00 to 15:00 on both
2017-2021 and 2022-2026 (0.7-4.4%), mostly with more calls right, and on 2022-2026 the
pinball loss 0.4-1.6% (see README). Today's levels are the high and low so far plus those extras times today's
yardstick:

- done: (weighted) share of past days whose HOD (or LOD) was already in at this point
- levels: if it goes further, the prices it reached on 75% / 50% / 25% of the past
  days that did go further (levels over all days would collapse onto the current
  high/low once most days are done, and be "reached" trivially)

Run: python levels.py [DATE] [HOUR]   (HOUR = after that hour's candle, "open" for the
     pre-open view; omit for the latest candle of DATE). Prints the levels and the brightest
     heatmap levels as prices, and saves the heatmap as hodlod.png
     python levels.py backtest        (walk-forward calibration on all the data)
     --2y on either: learn only from the last two years before the day (as the original tool)
"""

import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd
from scipy.stats import norm

import lse_source
from quantistat import REACH, daily_stats, load_candles, today_market

CHECKPOINTS = [None, 2, 5, 9, 12, 15]  # None = before the open
QUANTILES = [0.25, 0.5, 0.75]
# Day range / prior 5-day average on event days vs 1.04 on ordinary days (2016-2026).
# Tried and rejected, each scored with pinball loss on 2017-2021 and 2022+: matching the
# share of a normal range already used (no gain), and forecasting FOMC/CPI days from past
# FOMC/CPI days only (better on 2022+, worse on 2017-2021), so events only get a warning.
EVENT_SIZE = {"FOMC": 1.3, "CPI": 1.2}
K_NEAREST = 150  # 300 was worse on 2018-2021 from 9:00 on
MIN_DAYS = 2  # heatmap cells where fewer similar days ended are hidden: one day is noise
# Log-scale weights of yesterday's, the 5-day and the 22-day average Parkinson volatility in the
# yardstick (HAR, Corsi 2009), fit on 2016-2021 by regressing the log of each day's range on them;
# HAR_SCALE (e^intercept) only makes it read as a typical day's range in points.
HAR = (0.59, 0.29, 0.10)
HAR_SCALE = 1.57
# Share of a day's variance (hourly Parkinson, 2016-2021) still to come after each hour's candle,
# for the random walk the "already in" odds blend in (see rw_done).
REMAINING = np.array([0.981, 0.962, 0.937, 0.898, 0.868, 0.845, 0.819, 0.794, 0.741, 0.637, 0.533, 0.455,
                      0.391, 0.331, 0.264, 0.146, 0.12, 0.12, 0.097, 0.08, 0.057, 0.028, 0.012, 0.0])
RW_SIGMA = 1 / np.sqrt(8 / np.pi)  # a random walk's daily sd per unit of its expected range (the yardstick)


def rw_done(dist: float, hour: int) -> float:
    """Chance a driftless random walk never gets back above a high `dist` yardsticks above price in
    the rest of the day (reflection principle: its maximum is |N(0, sd)|). ES intraday is close to
    one (Mok, Lam & Li 2000): averaging this with the analogs' share cut the log loss of "already
    in" 2-9% at every checkpoint from 2:00 on, 2017-2021 and 2022-2026 alike (paired t -3.6 to
    -8.1), with more calls right at 5:00 and 15:00. Blending the levels too did not help."""
    sd = RW_SIGMA * np.sqrt(REMAINING[hour])
    return 1.0 if sd <= 0 else 2 * norm.cdf(dist / sd) - 1


def through_hour(candles: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Running high, running low and last close of each calendar day after each hour
    (rows: days, columns: 0-23)."""
    keys = [candles.index.date, candles.index.hour]
    by_hour = lambda s, f: getattr(s.groupby(keys), f)().unstack().reindex(columns=range(24))
    return (by_hour(candles.High, "max").cummax(axis=1).ffill(axis=1),
            by_hour(candles.Low, "min").cummin(axis=1).ffill(axis=1),
            by_hour(candles.Close, "last").ffill(axis=1))


def position(hi: pd.DataFrame, lo: pd.DataFrame, close: pd.DataFrame, hour: int, bins: int = 5) -> pd.Series:
    """Which `bins`-th of the day's range so far price sits in after `hour` (0 = bottom);
    a flat range counts as the middle."""
    where = ((close[hour] - lo[hour]) / (hi[hour] - lo[hour]).where(hi[hour] > lo[hour])).fillna(0.5)
    return (where * bins).clip(upper=bins - 1).astype(int)


def wquantile(values: np.ndarray, weights: np.ndarray, q) -> np.ndarray:
    """Weighted quantile; equal weights give np.quantile's (linear) answer, zero weights don't count."""
    keep = weights > 0
    order = np.argsort(values[keep])
    v, w = values[keep][order], weights[keep][order]
    if len(v) == 1:
        return np.full(np.shape(q), v[0])
    mid = np.cumsum(w) - w / 2 - w[0] / 2  # each value at the middle of its weight
    return np.interp(q, mid / mid[-1], v)


def similar(where: np.ndarray, near: np.ndarray, today_where: int, today_near: np.ndarray) -> np.ndarray:
    """Weight of each past day: half shared by the days in today's fifth of the range so far,
    half by the K_NEAREST days closest to today in (points below the high, points above the
    low) so far, in yardsticks and standardized."""
    same = where == today_where
    dist = (((near - today_near) / (near.std(axis=0) + 1e-9)) ** 2).sum(axis=1)
    nearest = np.zeros(len(near), bool)
    nearest[np.argsort(dist, kind="stable")[:K_NEAREST]] = True
    return same / max(same.sum(), 1) + nearest / nearest.sum()


def nearness(hi_now, lo_now, close_now, yardstick) -> np.ndarray:
    """(points below the high so far, points above the low so far) in yardsticks."""
    return np.column_stack([(hi_now - close_now) / yardstick, (close_now - lo_now) / yardstick])


def pinball(actual: float, past: np.ndarray, now: float, sign: int, today_range: float, w: np.ndarray | None = None) -> float:
    """Quantile (pinball) loss of the 25/50/75% levels over all (weighted) past days: one proper
    score for the whole forecast, lower is better."""
    y = sign * (actual - now) / today_range
    w = np.ones(len(past)) if w is None else w
    return sum(max(q * (y - x), (q - 1) * (y - x)) for q, x in zip(QUANTILES, wquantile(past, w, QUANTILES))) * today_range


def extras(stats: pd.DataFrame, hi: pd.DataFrame, lo: pd.DataFrame, hour: int | None) -> pd.DataFrame:
    """How far the HOD/LOD still went beyond the high/low known at `hour`, in yardsticks (r5 column)."""
    hi_now = stats.open if hour is None else hi[hour].reindex(stats.index)
    lo_now = stats.open if hour is None else lo[hour].reindex(stats.index)
    return pd.DataFrame({"up": (stats.high - hi_now) / stats.r5, "down": (lo_now - stats.low) / stats.r5})


def odds(extra: np.ndarray, now: float, sign: int, today_range: float,
         w: np.ndarray | None = None, rw: float | None = None) -> tuple[float, list[float]]:
    """(share already done, levels reached on 75/50/25% of the days that went further), each past
    day counted by its weight; the share is averaged with rw (rw_done) when given."""
    w = np.ones(len(extra)) if w is None else w
    more = (extra > 1e-9) & (w > 0)
    if not more.any():
        return 1.0 if rw is None else (1 + rw) / 2, [np.nan] * len(REACH)
    done = 1 - w[more].sum() / w.sum()
    return (done if rw is None else (done + rw) / 2,
            [now + sign * wquantile(extra[more], w[more], 1 - p) * today_range for p in REACH])


def heat(extra: np.ndarray, now: float, sign: int, today_range: float,
         origin: float) -> list[tuple[float, int]]:
    """The price heatmap: how many similar days that went further had their HOD (LOD) in each
    1-point cell, in today's prices. Cells sit a whole number of points from `origin` (the open);
    a HOD (LOD) that rounds onto the open counts in the cell 1 point above (below) it."""
    if np.isnan(today_range):
        return []
    points = np.round(now - origin + sign * extra[extra > 1e-9] * today_range)
    prices = origin + np.where(points == 0, sign, points)
    return [(float(p), int(c)) for p, c in zip(*np.unique(prices, return_counts=True))]


def brightest(cells: list[tuple[float, int]], now: float, top: int = 3) -> list[tuple[float, int]]:
    """The `top` heatmap cells where the most similar days ended (nearest to price first on a tie)."""
    return sorted(sorted(cells, key=lambda c: (-c[1], abs(c[0] - now)))[:top], key=lambda c: c[0])


def plot_heat(f: dict, open_price: float, title: str):
    """QuantiStat-style "HOD/LOD Price Based" heatmap of one forecast row (see day_lines): points
    from the 00:00 open, a line per 1-point cell where 2+ (MIN_DAYS) similar days ended and at least half as
    many as in that side's brightest cell (fewer would bury it), brighter and thicker = more days; dashed = the 75/50/25% levels; thin white = the open and the high/low so far."""
    import matplotlib.pyplot as plt
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 7))
    cells = [cell for side in ("HOD", "LOD") for cell in f[side]["heat"]
             if cell[1] >= max(MIN_DAYS, 0.5 * max(c for _, c in f[side]["heat"]))]
    norm = Normalize(MIN_DAYS, max([c for _, c in cells], default=MIN_DAYS + 1))
    for price, count in cells:
        ax.axhline(price - open_price, color=plt.cm.viridis(norm(count)), linewidth=2 + 4 * norm(count))
    for side in ("HOD", "LOD"):
        for lvl in f[side]["levels"]:
            if not np.isnan(lvl):
                ax.axhline(lvl - open_price, color="tab:cyan", linestyle="--", linewidth=1)
    for y in (0, f["high"] - open_price, f["low"] - open_price):
        ax.axhline(y, color="white", linewidth=1)
    ax.set_title(title)
    ax.set_ylabel("points from the 00:00 open")
    ax.secondary_yaxis("right", functions=(lambda y: y + open_price, lambda p: p - open_price)).set_ylabel("price")
    ax.set_xticks([])
    ax.grid(alpha=0.2)
    fig.colorbar(ScalarMappable(norm, "viridis"), ax=ax, label="similar days that ended there", pad=0.12)
    return fig


def forecast(ex: pd.DataFrame, high_so_far: float, low_so_far: float, today_range: float, origin: float,
             w: np.ndarray | None = None, rw: tuple[float, float] | None = None) -> dict:
    """Per side: done, levels, and line = the median final HOD/LOD over all similar days (the
    best single guess; it sits on the high/low so far once most similar days were done). rw =
    the random walk's "already in" for the HOD and the LOD, averaged into done."""
    w = np.ones(len(ex)) if w is None else w
    keep = ex.notna().all(axis=1).to_numpy() & (w > 0)
    ex, w = ex[keep], w[keep]
    return {side: dict(zip(["done", "levels"], odds(ex[col].to_numpy(), now, sign, today_range, w,
                                                    None if rw is None else rw[k])),
                       line=now + sign * wquantile(ex[col].to_numpy(), w, 0.5) * today_range,
                       heat=heat(ex[col].to_numpy(), now, sign, today_range, origin))
            for side, col, now, sign, k in [("HOD", "up", high_so_far, 1, 0), ("LOD", "down", low_so_far, -1, 1)]}


def day_lines(candles: pd.DataFrame, stats: pd.DataFrame, target: date, today_range: float,
              lookback_days: int | None = None) -> list[dict]:
    """The forecast before the open and after each of target's hourly candles so far, each from
    earlier days only (the last lookback_days if given): how the HOD/LOD line moved through the day."""
    hi, lo, close = through_hour(candles)
    day = candles[candles.index.date == target]
    out = []
    for hour in [None, *range(day.index[-1].hour + 1)]:  # hours without a candle (17:00 halt) carry on
        first = target - timedelta(days=lookback_days) if lookback_days else date.min
        history = stats[[first <= d < target for d in stats.index]]
        ex, w, today_near = extras(history, hi, lo, hour), np.ones(len(history)), np.zeros(2)
        if hour is not None:
            where = position(hi, lo, close, hour)
            near = nearness(*(x[hour].reindex(history.index) for x in (hi, lo, close)), history.r5)
            ok = ~np.isnan(near).any(axis=1) & ex.notna().all(axis=1).to_numpy()  # same days as walk_forward
            today_near = nearness(hi.loc[target, hour], lo.loc[target, hour], close.loc[target, hour], today_range)[0]
            ex, w = ex[ok], similar(where.reindex(history.index).to_numpy()[ok], near[ok], where[target], today_near)
        high = day.Open.iloc[0] if hour is None else hi.loc[target, hour]
        low = day.Open.iloc[0] if hour is None else lo.loc[target, hour]
        out.append({"hour": hour, "high": high, "low": low, "n": int((w > 0).sum()),
                    **forecast(ex, high, low, today_range, day.Open.iloc[0], w,
                               None if hour is None else [rw_done(x, hour) for x in today_near])})
    return out


def yardstick(park: pd.Series) -> pd.Series:
    """Each day's typical range in points from earlier days' hourly (Parkinson) volatility, HAR-style.
    A constant factor would cancel anyway: levels are past extras in yardsticks times today's."""
    p = park.shift()
    return HAR_SCALE * p ** HAR[0] * p.rolling(5).mean() ** HAR[1] * p.rolling(22).mean() ** HAR[2]


def use_yardstick(stats: pd.DataFrame) -> None:
    """Rewrite stats.r5 (the scale column the forecast reads) with the HAR yardstick on the same days.
    Walk-forward on LSE 2022-2026 it cut the pinball loss 2.2% at the open (paired t -4.9), 1.2% at
    2:00 and 5:00, ~0 at 9:00 and 12:00, 0.6% at 15:00 vs the 5-day range (2017-2021: 1-3%)."""
    stats["r5"] = yardstick(stats.park).where(stats.r5.notna())


def today_yardstick(stats: pd.DataFrame, target: date) -> float:
    """The yardstick of target from the kept days before it, also when target itself is not kept."""
    park = stats.park[[d < target for d in stats.index]]
    return yardstick(pd.concat([park, pd.Series([np.nan], index=[target])])).iloc[-1]


def walk_forward(stats: pd.DataFrame, hi: pd.DataFrame, lo: pd.DataFrame, close: pd.DataFrame,
                 warmup: int = 250, lookback_days: int | None = None) -> pd.DataFrame:
    """Each day forecast only from earlier days (the last lookback_days if given); did the HOD/LOD
    reach each level?"""
    days = np.array(stats.index)
    rows = []
    for hour in CHECKPOINTS:
        ex = extras(stats, hi, lo, hour).to_numpy()
        hi_now = (stats.open if hour is None else hi[hour].reindex(stats.index)).to_numpy()
        lo_now = (stats.open if hour is None else lo[hour].reindex(stats.index)).to_numpy()
        where = (np.zeros(len(stats), int) if hour is None
                 else position(hi, lo, close, hour).reindex(stats.index).to_numpy(int))
        close_now = stats.open if hour is None else close[hour].reindex(stats.index)
        near = nearness(hi_now, lo_now, close_now.to_numpy(), stats.r5.to_numpy())
        for i in range(warmup, len(stats)):
            ok = ~np.isnan(ex[:i]).any(axis=1) & ~np.isnan(near[:i]).any(axis=1)
            if lookback_days:
                ok &= days[:i] >= days[i] - timedelta(days=lookback_days)
            past = ex[:i][ok]
            w = np.ones(len(past)) if hour is None else similar(where[:i][ok], near[:i][ok], where[i], near[i])
            day, r = stats.iloc[i], stats.r5.iloc[i]
            row = {"hour": "open" if hour is None else f"{hour}:00", "day": stats.index[i]}
            for side, col, now, sign, actual in [("HOD", 0, hi_now[i], 1, day.high), ("LOD", 1, lo_now[i], -1, day.low)]:
                done, lvls = odds(past[:, col], now, sign, r, w, None if hour is None else rw_done(near[i][col], hour))
                went_further = sign * (actual - now) > 1e-9
                row |= {f"{side}_done_pred": done, f"{side}_done_real": float(not went_further),
                        **{f"{side}_{int(p * 100)}": float(sign * (actual - lvl) >= 0) if went_further and not np.isnan(lvl) else np.nan
                           for p, lvl in zip(REACH, lvls)},
                        f"{side}_miss": abs(actual - (line := now + sign * wquantile(past[:, col], w, 0.5) * r)),
                        # once price reached a line above/below the high/low so far, how much further it went
                        f"{side}_past_line": sign * (actual - line) if sign * (actual - line) >= 0 and line != now else np.nan,
                        f"{side}_pinball": pinball(actual, past[:, col], now, sign, r, w)}
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    candles = load_candles()
    stats = daily_stats(candles)
    use_yardstick(stats)
    hi, lo, close = through_hour(candles)
    args = [a for a in sys.argv[1:] if a != "--2y"]
    lookback = 730 if "--2y" in sys.argv else None  # only the last two years, like the original tool
    if args[:1] == ["backtest"]:
        result = walk_forward(stats.dropna(), hi, lo, close, lookback_days=lookback)
        print(f"{result.day.nunique()} days, {result.day.min()} .. {result.day.max()}, scaled by the HAR yardstick")
        print("*_done_pred vs *_done_real: forecast vs real share of days already done at that hour;")
        print("HOD_75 etc.: on days that went further, share reaching the '75%' level (honest: ~0.75);")
        print("*_miss: average points between the overall median forecast (the line) and the real HOD/LOD;")
        print("*_past_line: on days price reached a line away from the high/low so far, points it went beyond it\n")
        print(result.groupby("hour", sort=False).mean(numeric_only=True).round(3).to_string())
        sys.exit()
    try:
        events = lse_source.events()
    except OSError as e:  # the calendar only adds a warning; never block the forecast
        print(f"(event calendar unavailable: {e})")
        events = {}
    target = date.fromisoformat(args[0]) if args else today_market()
    day = candles[candles.index.date == target]
    hour = (day.index[-1].hour if len(day) else None) if len(args) < 2 else (
        None if args[1] == "open" else int(args[1]))
    if len(day) == 0 or day.index[0].hour != 0:
        sys.exit(f"No 00:00 candle for {target} yet: run after midnight New York time.")
    if hour is not None and hour > day.index[-1].hour:
        sys.exit(f"The {hour}:00 candle of {target} is not in yet (latest {day.index[-1].hour}:00).")
    open_price = day.Open.iloc[0]
    today_range = today_yardstick(stats, target)
    f = next(r for r in day_lines(candles[candles.index.date <= target], stats, target, today_range, lookback) if r["hour"] == hour)
    hod_now, lod_now = f["high"], f["low"]
    when = "before the open" if hour is None else f"after the {hour}:00 candle: high {hod_now:.2f}, low {lod_now:.2f}"
    kind = f"{events[target]} day, " if target in events else ""
    print(f"{target} {kind}open {open_price:.2f}, expected range {today_range:.1f}, {when}  ({f['n']} similar past days)")
    for side in ("HOD", "LOD"):
        lv = " / ".join(f"{x:.2f}" for x in f[side]["levels"])
        print(f"  {side}: chance it is already in {f[side]["done"]:.0%}; "
              f"if it goes further: {lv} (reached on 75% / 50% / 25% of those); best guess {f[side]['line']:.2f}")
    for side in ("HOD", "LOD"):
        now = f["high"] if side == "HOD" else f["low"]
        top = ", ".join(f"{p:.2f} ({c} days)" for p, c in brightest(f[side]["heat"], now))
        print(f"  {side} brightest levels: {top or 'none'}")
    title = f"HOD/LOD Price Based - {target} " + ("before the open" if hour is None else f"after {hour}:00")
    plot_heat(f, open_price, title).savefig("hodlod.png", dpi=120)
    print("  Saved hodlod.png")
    if target in events:
        print(f"  Warning: on past {events[target]} days the range ran ~{EVENT_SIZE[events[target]]}x normal and these "
              "levels were reached more often than stated (the 14:00 FOMC decision often sets the HOD/LOD late). "
              "Treat them as too tight. (Matching past event days instead did not hold up out of sample.)")
    if target < today_market():
        print(f"  actual: HOD {day.High.max():.2f} at {day.High.idxmax().hour}:00, "
              f"LOD {day.Low.min():.2f} at {day.Low.idxmin().hour}:00")

"""QuantiStat-style HOD/LOD statistics for ES, drawn with matplotlib.

Takes LSE's ten years of hourly ES candles and looks only at past
days on the same weekday as the target day (e.g. every Monday). backtest.py showed
this beats the original tool's same day-of-month, which leaves only ~16 noisy days.
A day is a calendar day in New York time (00:00-23:00), so it opens at the
00:00 candle and the previous day must have ended before running this.

- Time Based: at which hour the high (HOD) and the low (LOD) of the day formed,
  split by bias (bullish = closed above its open).
- Price Based: how many points from the open the HOD (above 0) and the LOD
  (below 0) landed, split by bias like Time Based. The original mixes both kinds of
  day in one map; backtest.py showed splitting cuts the miss from ~34 to ~27 points.
- Text plan: per bias, the most common HOD/LOD hours and the distances the HOD/LOD
  reached on 75%, 50% and 25% of days (prices too, if you pass the 00:00 open).

Run: python quantistat.py [TARGET_DATE] [OPEN]   (default: today, distances only)
"""

import sys
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

import lse_source
from app import today_market

HOURS = range(24)
BIASES = [(True, "Bullish", "blue"), (False, "Bearish", "purple")]
REACH = [0.75, 0.5, 0.25]
# A continuous ES series flips between contracts around a roll, which shows up as a
# jump between two candles of the same day. Real hour-to-hour gaps are a few points;
# only the 18:00 reopen after the daily halt can gap for real.
MAX_GAP_POINTS = 25


def in_expiry_week(d: date) -> bool:
    """Monday to third Friday of Mar/Jun/Sep/Dec, when a continuous series can also mix the two
    contracts inside single candles, which the gap check can't see."""
    third_friday = 15 + (4 - date(d.year, d.month, 15).weekday()) % 7
    return d.month % 3 == 0 and third_friday - 4 <= d.day <= third_friday


def load_candles() -> pd.DataFrame:
    """Ten years of ES.F 1h bars from LSE."""
    return lse_source.fetch()


def daily_stats(candles: pd.DataFrame) -> pd.DataFrame:
    """One row per calendar day that opens at 00:00 (drops Sunday's 18:00 session start),
    outside expiry weeks and without a contract-roll jump."""
    same_day = candles.index.date[1:] == candles.index.date[:-1]
    jumps = (candles.Open - candles.Close.shift()).abs().iloc[1:] > MAX_GAP_POINTS
    bad = jumps & same_day & (candles.index[1:].hour != 18)
    rolled_days = set(bad[bad].index.date)
    days = candles.groupby(candles.index.date)
    stats = pd.DataFrame({
        "open": days.Open.first(),
        "high": days.High.max(),
        "low": days.Low.min(),
        "close": days.Close.last(),
        "hod_hour": days.High.idxmax().map(lambda ts: ts.hour),
        "lod_hour": days.Low.idxmin().map(lambda ts: ts.hour),
        "first_hour": days.apply(lambda d: d.index[0].hour),
        # Parkinson volatility from the day's hourly high/low, in points: levels.py's yardstick input
        "park": np.sqrt((np.log(candles.High / candles.Low) ** 2).groupby(candles.index.date).sum()
                        / (4 * np.log(2))) * days.Open.first(),
    })
    stats["bullish"] = stats.close > stats.open
    keep = (stats.first_hour == 0) & ~stats.index.isin(rolled_days) & ~stats.index.map(in_expiry_week)
    stats = stats[keep].drop(columns="first_hour")
    stats["r5"] = (stats.high - stats.low).rolling(5).mean().shift()  # known before the day opens
    return stats


def recent_range(stats: pd.DataFrame, target: date) -> float:
    """Average high-low range of the 5 days before target: today's volatility yardstick."""
    before = stats[[d < target for d in stats.index]]
    return (before.high - before.low).tail(5).mean()


def same_weekday(stats: pd.DataFrame, target: date) -> pd.DataFrame:
    return stats[[d.weekday() == target.weekday() and d < target for d in stats.index]]


def level_counts(stats: pd.DataFrame, today_range: float) -> pd.Series:
    """How many times each HOD/LOD distance from the open (rounded to a point) occurred,
    in today's points: each day is rescaled by today's 5-day range over its own."""
    k = today_range / stats.r5
    distances = pd.concat([(stats.high - stats.open) * k, (stats.low - stats.open) * k]).round()
    return distances.value_counts().sort_index()


def reach_levels(days: pd.DataFrame, today_range: float) -> dict[str, list[float]]:
    """Distances from the open that the HOD and the LOD reached on 75%, 50% and 25% of days,
    rescaled to today's volatility (raw points from 2016 would be far too small today)."""
    k = today_range / days.r5
    return {"HOD": [((days.high - days.open) * k).quantile(1 - p) for p in REACH],
            "LOD": [((days.low - days.open) * k).quantile(p) for p in REACH]}


def plot_time_based(stats: pd.DataFrame):
    plt.style.use("dark_background")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for row, (bullish, name, color) in enumerate(BIASES):
        days = stats[stats.bullish == bullish]
        for ax, kind in zip(axes[row], ["HOD", "LOD"]):
            ax.hist(days[f"{kind.lower()}_hour"], bins=range(25), color=color, edgecolor="white")
            ax.set_title(f"{kind} If {name} Bias (n={len(days)})")
            ax.set_xlabel("Time")
            ax.set_ylabel("Frequency")
            ax.set_xticks(HOURS, [f"{h}:00" for h in HOURS], rotation=45)
    fig.tight_layout()
    return fig


def plot_price_based(stats: pd.DataFrame, today_range: float):
    plt.style.use("dark_background")
    groups = {name: stats[stats.bullish == bullish] for bullish, name, _ in BIASES}
    counts = {name: level_counts(days, today_range) for name, days in groups.items()}
    norm = Normalize(0, max(c.max() for c in counts.values() if len(c)))
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    for ax, (name, levels) in zip(axes, counts.items()):
        for points, count in levels.items():
            ax.axhline(points, color=plt.cm.viridis(norm(count)), linewidth=2 * count)
        ax.set_title(f"HOD/LOD If {name} Bias (n={len(groups[name])})")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel(f"points (scaled to today's 5-day range, {today_range:.0f})")
    fig.colorbar(ScalarMappable(norm, "viridis"), ax=axes, label="heatmap")
    return fig


def print_plan(stats: pd.DataFrame, today_range: float, open_price: float | None):
    for bullish, name, _ in BIASES:
        days = stats[stats.bullish == bullish]
        print(f"\n{name} bias ({len(days)} days)")
        for kind, levels in reach_levels(days, today_range).items():
            hours = ", ".join(f"{h}:00" for h in days[f"{kind.lower()}_hour"].value_counts().index[:2])
            reached = " / ".join(f"{lvl:+.1f}" + (f" = {open_price + lvl:.2f}" if open_price else "") for lvl in levels)
            print(f"  {kind}: most often at {hours}; reached {reached} on 75% / 50% / 25% of days")


if __name__ == "__main__":
    target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else today_market()
    open_price = float(sys.argv[2]) if len(sys.argv) > 2 else None
    all_days = daily_stats(load_candles())
    today_range = recent_range(all_days, target)
    stats = same_weekday(all_days, target)
    print(f"{len(stats)} past {target:%A}s, from {stats.index[0]}; last 5 days' average range {today_range:.1f} points")
    print_plan(stats, today_range, open_price)
    plot_time_based(stats).savefig("time_based.png")
    plot_price_based(stats, today_range).savefig("price_based.png")
    print("Saved time_based.png and price_based.png")
    plt.show()

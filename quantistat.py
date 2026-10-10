"""QuantiStat-style HOD/LOD statistics for ES=F, drawn with matplotlib.

Takes the two years of hourly candles that app.py serves and looks only at past
days with the same day-of-month as the target day (e.g. every 2nd for Jan 2).
A day is a calendar day in New York time (00:00-23:00), so it opens at the
00:00 candle and the previous day must have ended before running this.

- Time Based: at which hour the high (HOD) and the low (LOD) of the day formed,
  split by bias (bullish = closed above its open).
- Price Based: how many points from the open the HOD (above 0) and the LOD
  (below 0) landed. Your bias picks which half to read.

Run: python quantistat.py [TARGET_DATE]   (default: today)
"""

import sys
from datetime import date

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

from app import fetch_candles, today_market

HOURS = range(24)
# Yahoo's continuous ES=F flips between contracts around a roll, which shows up as a
# jump between two candles of the same day. Real hour-to-hour gaps are a few points;
# only the 18:00 reopen after the daily halt can gap for real.
MAX_GAP_POINTS = 25


def in_expiry_week(d: date) -> bool:
    """Monday to third Friday of Mar/Jun/Sep/Dec, when Yahoo also mixes the two
    contracts inside single candles, which the gap check can't see."""
    third_friday = 15 + (4 - date(d.year, d.month, 15).weekday()) % 7
    return d.month % 3 == 0 and third_friday - 4 <= d.day <= third_friday


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
    })
    stats["bullish"] = stats.close > stats.open
    keep = (stats.first_hour == 0) & ~stats.index.isin(rolled_days) & ~stats.index.map(in_expiry_week)
    return stats[keep].drop(columns="first_hour")


def same_day_of_month(stats: pd.DataFrame, target: date) -> pd.DataFrame:
    return stats[[d.day == target.day and d < target for d in stats.index]]


def level_counts(stats: pd.DataFrame) -> pd.Series:
    """How many times each HOD/LOD distance from the open (rounded to a point) occurred."""
    distances = pd.concat([stats.high - stats.open, stats.low - stats.open]).round()
    return distances.value_counts().sort_index()


def plot_time_based(stats: pd.DataFrame):
    plt.style.use("dark_background")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for row, (bullish, name, color) in enumerate([(True, "Bullish", "blue"), (False, "Bearish", "purple")]):
        days = stats[stats.bullish == bullish]
        for ax, kind in zip(axes[row], ["HOD", "LOD"]):
            ax.hist(days[f"{kind.lower()}_hour"], bins=range(25), color=color, edgecolor="white")
            ax.set_title(f"{kind} If {name} Bias (n={len(days)})")
            ax.set_xlabel("Time")
            ax.set_ylabel("Frequency")
            ax.set_xticks(HOURS, [f"{h}:00" for h in HOURS], rotation=45)
    fig.tight_layout()
    return fig


def plot_price_based(stats: pd.DataFrame):
    plt.style.use("dark_background")
    counts = level_counts(stats)
    norm = Normalize(0, counts.max())
    fig, ax = plt.subplots(figsize=(9, 6))
    for points, count in counts.items():
        ax.axhline(points, color=plt.cm.viridis(norm(count)), linewidth=2 * count)
    fig.colorbar(ScalarMappable(norm, "viridis"), ax=ax, label="heatmap")
    ax.set_title(f"HOD/LOD Price Based (n={len(stats)})")
    ax.set_ylabel("points")
    ax.grid(alpha=0.2)
    return fig


if __name__ == "__main__":
    target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else today_market()
    stats = same_day_of_month(daily_stats(fetch_candles(today_market())), target)
    print(f"{len(stats)} past days on day {target.day} of the month")
    print(stats.to_string())
    plot_time_based(stats).savefig("time_based.png")
    plot_price_based(stats).savefig("price_based.png")
    print("Saved time_based.png and price_based.png")
    plt.show()

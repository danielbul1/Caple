"""Seasonal tendencies for ES, like market-bulls.com's page that the video uses for bias.

For a target day, average the point change of the dates within 3 days of it over the
10, 5 and 2 years before its year (a single date is often a weekend) (the site refreshes on January 1, so a year never sees
itself). The bias is the sign; "agree" calls only when all three windows point the
same way, which is how the video reads it ("2, 5 and 10 year data all show a sell off").
Daily closes (each New York day's last 1h close) come from LSE, which starts mid 2016, so
the 10-year window only uses the years it has.

Run: python seasonal.py [DATE]   -> prints the bias and saves seasonal.png
"""

import sys
from bisect import bisect_left
from datetime import date, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import lse_source
from app import today_market

WINDOWS = [10, 5, 2]
COLORS = {10: "purple", 5: "tab:blue", 2: "tab:green"}


def daily_changes() -> pd.Series:
    close = lse_source.fetch().Close
    daily = close.groupby(close.index.date).last()
    daily.index = pd.to_datetime(daily.index)
    return daily.diff().dropna()


def by_date(changes: pd.Series) -> pd.DataFrame:
    """Rows: years. Columns: (month, day). Values: that date's point change."""
    idx = changes.index
    return changes.groupby([idx.year, idx.month, idx.day]).sum().unstack([1, 2]).sort_index(axis=1)


def seasonal_change(table: pd.DataFrame, d: date, years: int, around: int = 3) -> float:
    near = [(d + timedelta(days=k)) for k in range(-around, around + 1)]
    keys = [(x.month, x.day) for x in near if (x.month, x.day) in table.columns]
    values = table.loc[d.year - years:d.year - 1, keys].to_numpy().ravel() if keys else []
    return np.nanmean(values) if np.isfinite(values).any() else np.nan


def rules(table: pd.DataFrame, dates) -> pd.DataFrame:
    """1.0 = bullish, 0.0 = bearish, NaN = no call, per window and when all agree."""
    sign = lambda x: np.nan if np.isnan(x) or x == 0 else float(x > 0)
    calls = pd.DataFrame({f"seasonal_{n}y": [sign(seasonal_change(table, d, n)) for d in dates]
                          for n in WINDOWS}, index=list(dates))
    agree = calls.nunique(axis=1, dropna=False).eq(1) & calls.notna().all(axis=1)
    calls["seasonal_agree"] = calls.iloc[:, 0].where(agree)
    return calls


def seasonal_path(table: pd.DataFrame, year: int, years: int) -> pd.Series:
    """Cumulative average point change through the calendar year."""
    return table.loc[year - years:year - 1].mean().fillna(0).cumsum()  # no trading that date = no change


def plot(table: pd.DataFrame, target: date):
    plt.style.use("dark_background")
    fig, (year_ax, month_ax) = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={"width_ratios": [2, 1]})
    for n in WINDOWS:
        path = seasonal_path(table, target.year, n)
        year_ax.plot(range(len(path)), path.values, color=COLORS[n], label=f"{n} Years")
        month = table.loc[target.year - n:target.year - 1, target.month].mean().fillna(0).cumsum()
        month_ax.plot(month.index, month.values, color=COLORS[n], label=f"{n}y")
        if n == WINDOWS[0]:
            year_ax.axvline(bisect_left(list(path.index), (target.month, target.day)), color="red")
            month_ax.axvline(target.day, color="red")
    year_ax.set_xticks([path.index.get_loc((m, path[m].index[0])) for m in range(1, 13)],
                       ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    year_ax.set_title(f"Seasonal Tendencies Yearly - ES ({target.year})")
    month_ax.set_title(f"ES Seasonals {target:%B}")
    month_ax.set_xlabel("Days this month")
    for ax in (year_ax, month_ax):
        ax.set_ylabel("points")
        ax.grid(alpha=0.2)
        ax.legend()
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else today_market()
    table = by_date(daily_changes())
    for n in WINDOWS:
        print(f"{n:>2}y average change on {target:%b %d}: {seasonal_change(table, target, n):+.1f} points")
    call = rules(table, [target]).iloc[0].seasonal_agree
    print("Bias:", {1.0: "bullish", 0.0: "bearish"}.get(call, "no call (windows disagree)"))
    months = pd.DataFrame({f"{n} Years": table.loc[target.year - n:target.year - 1]
                           .T.groupby(level=0).sum().T.mean() for n in WINDOWS}).T
    months.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    print("\nAverage change per month (points):\n" + months.round(1).to_string())
    plot(table, target).savefig("seasonal.png")
    print("Saved seasonal.png")
    plt.show()

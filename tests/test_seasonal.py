from datetime import date

import numpy as np
import pandas as pd

import seasonal


def changes(values):
    """{date: point change} -> Series indexed by Timestamp, like daily close diffs."""
    return pd.Series(list(values.values()), index=pd.to_datetime(list(values)))


def test_seasonal_change_averages_dates_around_the_day_in_the_years_before_only():
    ch = changes({"2023-01-02": 50.0, "2024-01-02": -10.0, "2025-01-02": 30.0, "2026-01-02": 999.0})
    table = seasonal.by_date(ch)
    assert seasonal.seasonal_change(table, date(2026, 1, 2), 2) == 10.0   # 2024, 2025; not 2026 itself
    assert seasonal.seasonal_change(table, date(2026, 1, 2), 10) == 70 / 3
    assert seasonal.seasonal_change(table, date(2026, 1, 4), 2) == 10.0   # a weekend uses the dates around it
    assert np.isnan(seasonal.seasonal_change(table, date(2026, 1, 20), 2))


def test_rules_call_only_when_all_windows_agree():
    ch = changes({f"{y}-03-10": (5.0 if y >= 2020 else -1.0) for y in range(2010, 2026)}
                 | {f"{y}-03-11": 5.0 for y in range(2010, 2026)})
    r = seasonal.rules(seasonal.by_date(ch), [date(2026, 3, 10), date(2026, 3, 11)])
    # Mar 10: 10y mean (2016-2025) = (4*-1 + 6*5)/10 = 2.6 > 0, 5y and 2y positive -> all bullish
    assert r.loc[date(2026, 3, 10), "seasonal_agree"] == 1.0
    assert r.loc[date(2026, 3, 11), "seasonal_agree"] == 1.0


def test_rules_make_no_call_when_windows_disagree():
    ch = changes({f"{y}-03-10": (-5.0 if y >= 2024 else 5.0) for y in range(2010, 2026)})
    r = seasonal.rules(seasonal.by_date(ch), [date(2026, 3, 10)])
    assert r.loc[date(2026, 3, 10), "seasonal_10y"] == 1.0
    assert r.loc[date(2026, 3, 10), "seasonal_2y"] == 0.0
    assert np.isnan(r.loc[date(2026, 3, 10), "seasonal_agree"])


def test_seasonal_path_is_the_cumulative_average_through_the_year():
    ch = changes({"2024-01-02": 10.0, "2024-01-03": -4.0, "2025-01-02": 20.0, "2025-01-03": 0.0})
    path = seasonal.seasonal_path(seasonal.by_date(ch), 2026, 2)
    assert path.tolist() == [15.0, 13.0]

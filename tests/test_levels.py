from datetime import date

import pandas as pd

import levels


def candles(rows):
    idx = pd.DatetimeIndex([r[0] for r in rows]).tz_localize("America/New_York")
    return pd.DataFrame([r[1:] for r in rows], index=idx, columns=["Open", "High", "Low", "Close"])


def test_through_hour_is_the_running_high_and_low_by_each_hour():
    df = candles([("2026-11-10 00:00", 100, 105, 99, 101), ("2026-11-10 01:00", 101, 103, 95, 96),
                  ("2026-11-10 03:00", 96, 110, 96, 108)])
    hi, lo, close = levels.through_hour(df)
    day = date(2026, 11, 10)
    assert [hi.loc[day, h] for h in (0, 1, 2, 3, 23)] == [105, 105, 105, 110, 110]
    assert [lo.loc[day, h] for h in (0, 1, 2, 3)] == [99, 95, 95, 95]
    assert [close.loc[day, h] for h in (1, 2, 3)] == [96, 96, 108]
    # After 1:00 price (96) sits in the lower half of 95..105; after 3:00 (108) in the upper half of 95..110.
    assert levels.upper_half(hi, lo, close, 1).loc[day] == False
    assert levels.upper_half(hi, lo, close, 3).loc[day] == True


def test_extras_measure_what_was_still_to_come_in_5_day_ranges():
    stats = pd.DataFrame({"open": [100.0], "high": [110.0], "low": [95.0], "r5": [5.0]}, index=[date(2026, 11, 10)])
    hi = pd.DataFrame({1: [105.0]}, index=stats.index)
    lo = pd.DataFrame({1: [95.0]}, index=stats.index)
    ex = levels.extras(stats, hi, lo, 1)
    assert ex.loc[date(2026, 11, 10)].tolist() == [1.0, 0.0]  # 5 more points up = one range; low already in
    pre_open = levels.extras(stats, hi, lo, None)               # before 00:00 only the open is known
    assert pre_open.loc[date(2026, 11, 10)].tolist() == [2.0, 1.0]


def test_forecast_turns_history_into_todays_odds_and_prices():
    ex = pd.DataFrame({"up": [0.0, 0.0, 1.0, 2.0], "down": [0.0, 1.0, 1.0, 1.0]})
    f = levels.forecast(ex, high_so_far=200.0, low_so_far=190.0, today_range=10.0)
    assert f["HOD"]["done"] == 0.5 and f["LOD"]["done"] == 0.25
    # If it goes further: from the days that did (up 1 and 2 ranges), reached on 75% / 50% / 25% of them.
    assert f["HOD"]["levels"] == [212.5, 215.0, 217.5]
    assert f["LOD"]["levels"] == [180.0, 180.0, 180.0]

from datetime import date

import pandas as pd

import backtest as bt


def test_backtest_scores_each_day_only_from_earlier_days():
    stats = pd.DataFrame({
        "open": [100.0, 100.0, 100.0], "high": [110.0, 120.0, 112.0], "low": [95.0, 98.0, 99.0],
        "hod_hour": [10, 12, 10], "lod_hour": [2, 2, 2], "bullish": [True, True, True], "r5": [1.0] * 3,
    }, index=[date(2026, 1, 5), date(2026, 2, 5), date(2026, 3, 5)])  # Mon, Thu, Thu
    result = bt.backtest(stats, warmup=2).set_index("method")
    # Day-of-month and all days both see days 1-2: HOD hour 10 got half the weight, LOD hour 2 all of it,
    # and the median HOD distance (10, 20) = 15 misses the actual 12 by 3.
    assert result.loc["same day of month", ["time_score", "price_error"]].tolist() == [0.75, 3.0]
    assert result.loc["all days", ["time_score", "price_error"]].tolist() == [0.75, 3.0]
    # Same weekday sees only day 2 (Thursday).
    assert result.loc["same weekday", ["time_score", "price_error"]].tolist() == [0.5, 8.0]


def test_bearish_days_are_scored_on_the_low_side():
    stats = pd.DataFrame({
        "open": [100.0, 100.0], "high": [101.0, 101.0], "low": [80.0, 90.0],
        "hod_hour": [0, 0], "lod_hour": [15, 15], "bullish": [False, False], "r5": [1.0] * 2,
    }, index=[date(2026, 1, 5), date(2026, 10, 5)])  # both Monday the 5th
    result = bt.backtest(stats, warmup=1).set_index("method")
    assert result.loc["all days", ["time_score", "price_error"]].tolist() == [1.0, 10.0]


def test_price_levels_come_from_same_bias_days_and_coverage_is_reported():
    stats = pd.DataFrame({
        "open": [100.0, 100.0, 100.0], "high": [130.0, 101.0, 125.0], "low": [99.0, 60.0, 98.0],
        "hod_hour": [15, 0, 15], "lod_hour": [0, 15, 0], "bullish": [True, False, True], "r5": [1.0] * 3,
    }, index=[date(2026, 1, 5), date(2026, 10, 5), date(2027, 4, 5)])  # Mondays, all on the 5th
    row = bt.backtest(stats, warmup=2).set_index("method").loc["all days"]
    # Only the bullish day (+30) counts for a bullish day, not the bearish +1: the +25 day reached none of it.
    assert (row.price_error, row.reached_75, row.reached_50, row.reached_25) == (5.0, False, False, False)

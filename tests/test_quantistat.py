from datetime import date

import pandas as pd

import quantistat as qs


def candles(rows):
    """rows: (timestamp, open, high, low, close) in New York time."""
    idx = pd.DatetimeIndex([r[0] for r in rows]).tz_localize("America/New_York")
    return pd.DataFrame([r[1:] for r in rows], index=idx, columns=["Open", "High", "Low", "Close"])


def test_daily_stats_uses_calendar_day_and_skips_days_not_opening_at_midnight():
    df = candles([
        ("2026-10-04 18:00", 100, 105, 99, 101),   # Sunday session start: no 00:00 candle
        ("2026-10-05 00:00", 100, 102, 99, 101),
        ("2026-10-05 09:00", 101, 110, 100, 108),  # HOD at 9
        ("2026-10-05 15:00", 108, 109, 95, 97),    # LOD at 15, closes below open
    ])
    stats = qs.daily_stats(df)
    assert list(stats.index) == [date(2026, 10, 5)]
    day = stats.iloc[0]
    assert (day.open, day.high, day.low, day.close) == (100, 110, 95, 97)
    assert (day.hod_hour, day.lod_hour, day.bullish) == (9, 15, False)


def test_same_weekday_keeps_only_earlier_days_on_that_weekday():
    stats = pd.DataFrame({"open": [1, 2, 3, 4]},
                         index=[date(2026, 9, 28), date(2026, 9, 29), date(2026, 10, 5), date(2026, 10, 12)])
    # Mondays before Monday 2026-10-12; Tuesday 29th and the target itself are left out.
    assert list(qs.same_weekday(stats, date(2026, 10, 12)).index) == [date(2026, 9, 28), date(2026, 10, 5)]


def test_level_counts_rounds_distances_from_open_to_points():
    stats = pd.DataFrame({"open": [100.0, 200.0], "high": [110.25, 210.0], "low": [90.0, 189.75]})
    assert qs.level_counts(stats).to_dict() == {-10.0: 2, 10.0: 2}


def test_plots_build_like_quantistat():
    stats = pd.DataFrame({"open": [100.0, 100.0], "high": [110.0, 104.0], "low": [97.0, 90.0],
                          "hod_hour": [19, 0], "lod_hour": [13, 16], "bullish": [True, False]})
    time_fig = qs.plot_time_based(stats)
    assert [ax.get_title() for ax in time_fig.axes] == [
        "HOD If Bullish Bias (n=1)", "LOD If Bullish Bias (n=1)",
        "HOD If Bearish Bias (n=1)", "LOD If Bearish Bias (n=1)"]
    price_fig = qs.plot_price_based(stats)
    assert price_fig.axes[0].get_title() == "HOD/LOD Price Based (n=2)"
    assert len(price_fig.axes[0].lines) == 4  # one horizontal level per distinct distance


def test_time_bars_sit_on_their_clock_hour():
    stats = pd.DataFrame({"hod_hour": [9, 10, 10], "lod_hour": [0, 23, 23], "bullish": [True] * 3})
    hod = qs.plot_time_based(stats).axes[0]
    assert {(p.get_x(), p.get_height()) for p in hod.patches if p.get_height()} == {(9, 1), (10, 2)}


def test_daily_stats_drops_days_with_a_contract_roll_jump_but_keeps_the_1800_reopen():
    df = candles([
        ("2026-11-10 00:00", 100, 101, 99, 100),
        ("2026-11-10 01:00", 160, 161, 159, 160),  # Yahoo flips to the next contract mid-day
        ("2026-11-11 00:00", 100, 101, 99, 100),
        ("2026-11-11 16:00", 100, 101, 99, 100),
        ("2026-11-11 18:00", 140, 141, 139, 140),  # real gap after the 17:00 halt
    ])
    assert list(qs.daily_stats(df).index) == [date(2026, 11, 11)]


def test_titles_show_sample_size():
    stats = pd.DataFrame({"open": [100.0], "high": [110.0], "low": [90.0],
                          "hod_hour": [1], "lod_hour": [2], "bullish": [True]})
    assert qs.plot_time_based(stats).axes[0].get_title() == "HOD If Bullish Bias (n=1)"
    assert qs.plot_price_based(stats).axes[0].get_title() == "HOD/LOD Price Based (n=1)"


def test_daily_stats_drops_the_quarterly_expiry_week():
    # Sep 2025 expires Fri 19th: Yahoo mixes contracts inside candles all week (15th-19th).
    rows = [(f"2025-09-{day} 00:00", 100, 101, 99, 100) for day in (12, 15, 19, 22)]
    rows += [("2025-10-16 00:00", 100, 101, 99, 100)]  # not a quarterly month
    assert [d.day for d in qs.daily_stats(candles(rows)).index] == [12, 22, 16]

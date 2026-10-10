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
    stats = pd.DataFrame({"open": [100.0, 200.0], "high": [110.25, 210.0], "low": [90.0, 189.75], "r5": [10.0, 10.0]})
    assert qs.level_counts(stats, 10.0).to_dict() == {-10.0: 2, 10.0: 2}


def test_levels_are_rescaled_to_todays_volatility():
    # A +10 day when the 5-day range was 10 counts as +20 when today's 5-day range is 20.
    stats = pd.DataFrame({"open": [100.0], "high": [110.0], "low": [95.0], "r5": [10.0]})
    assert qs.level_counts(stats, 20.0).to_dict() == {-10.0: 1, 20.0: 1}


def test_daily_stats_adds_the_previous_five_days_average_range():
    rows = [(f"2026-11-{day:02d} 00:00", 100, 100 + rng, 100, 100) for day, rng in
            zip((2, 3, 4, 5, 6, 9), (10, 20, 30, 40, 50, 99))]
    assert qs.daily_stats(candles(rows)).r5.iloc[-1] == 30  # mean of 10..50, not today's 99


def test_plots_build_like_quantistat():
    stats = pd.DataFrame({"open": [100.0, 100.0], "high": [110.0, 104.0], "low": [97.0, 90.0], "r5": [1.0, 1.0],
                          "hod_hour": [19, 0], "lod_hour": [13, 16], "bullish": [True, False]})
    time_fig = qs.plot_time_based(stats)
    assert [ax.get_title() for ax in time_fig.axes] == [
        "HOD If Bullish Bias (n=1)", "LOD If Bullish Bias (n=1)",
        "HOD If Bearish Bias (n=1)", "LOD If Bearish Bias (n=1)"]
    price_fig = qs.plot_price_based(stats, 1.0)
    assert [ax.get_title() for ax in price_fig.axes[:2]] == [
        "HOD/LOD If Bullish Bias (n=1)", "HOD/LOD If Bearish Bias (n=1)"]
    # Each bias only shows its own days' levels: bullish +10/-3, bearish +4/-10.
    assert [sorted(line.get_ydata()[0] for line in ax.lines) for ax in price_fig.axes[:2]] == [[-3, 10], [-10, 4]]


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
    stats = pd.DataFrame({"open": [100.0], "high": [110.0], "low": [90.0], "r5": [1.0],
                          "hod_hour": [1], "lod_hour": [2], "bullish": [True]})
    assert qs.plot_time_based(stats).axes[0].get_title() == "HOD If Bullish Bias (n=1)"
    assert qs.plot_price_based(stats, 1.0).axes[0].get_title() == "HOD/LOD If Bullish Bias (n=1)"


def test_daily_stats_drops_the_quarterly_expiry_week():
    # Sep 2025 expires Fri 19th: Yahoo mixes contracts inside candles all week (15th-19th).
    rows = [(f"2025-09-{day} 00:00", 100, 101, 99, 100) for day in (12, 15, 19, 22)]
    rows += [("2025-10-16 00:00", 100, 101, 99, 100)]  # not a quarterly month
    assert [d.day for d in qs.daily_stats(candles(rows)).index] == [12, 22, 16]


def test_reach_levels_are_the_distances_75_50_25_percent_of_days_reached():
    days = pd.DataFrame({"open": [100.0] * 5, "high": [110.0, 120, 130, 140, 150], "low": [90.0, 80, 70, 60, 50], "r5": [1.0] * 5})
    assert qs.reach_levels(days, 1.0) == {"HOD": [20, 30, 40], "LOD": [-20, -30, -40]}

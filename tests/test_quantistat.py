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


def test_same_day_of_month_keeps_only_earlier_days_with_that_day_number():
    stats = pd.DataFrame({"open": [1, 2, 3, 4]},
                         index=[date(2026, 8, 2), date(2026, 8, 3), date(2026, 9, 2), date(2026, 10, 2)])
    assert list(qs.same_day_of_month(stats, date(2026, 10, 2)).index) == [date(2026, 8, 2), date(2026, 9, 2)]


def test_level_counts_rounds_distances_from_open_to_points():
    stats = pd.DataFrame({"open": [100.0, 200.0], "high": [110.25, 210.0], "low": [90.0, 189.75]})
    assert qs.level_counts(stats).to_dict() == {-10.0: 2, 10.0: 2}


def test_plots_build_like_quantistat():
    stats = pd.DataFrame({"open": [100.0, 100.0], "high": [110.0, 104.0], "low": [97.0, 90.0],
                          "hod_hour": [19, 0], "lod_hour": [13, 16], "bullish": [True, False]})
    time_fig = qs.plot_time_based(stats)
    assert [ax.get_title() for ax in time_fig.axes] == [
        "HOD If Bullish Bias", "LOD If Bullish Bias", "HOD If Bearish Bias", "LOD If Bearish Bias"]
    price_fig = qs.plot_price_based(stats)
    assert price_fig.axes[0].get_title() == "HOD/LOD Price Based"
    assert len(price_fig.axes[0].lines) == 4  # one horizontal level per distinct distance


def test_time_bars_sit_on_their_clock_hour():
    stats = pd.DataFrame({"hod_hour": [9, 10, 10], "lod_hour": [0, 23, 23], "bullish": [True] * 3})
    hod = qs.plot_time_based(stats).axes[0]
    assert {(p.get_x(), p.get_height()) for p in hod.patches if p.get_height()} == {(9, 1), (10, 2)}

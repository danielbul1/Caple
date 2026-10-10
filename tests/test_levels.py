from datetime import date

import numpy as np

import pandas as pd

import levels


def candles(rows):
    idx = pd.DatetimeIndex([r[0] for r in rows]).tz_localize("America/New_York")
    return pd.DataFrame([r[1:] for r in rows], index=idx, columns=["Open", "High", "Low", "Close"])


def test_position_of_a_flat_range_is_the_middle_bin():
    df = candles([("2026-11-10 00:00", 100, 100, 100, 100)])
    assert levels.position(*levels.through_hour(df), 0).loc[date(2026, 11, 10)] == 2


def test_through_hour_is_the_running_high_and_low_by_each_hour():
    df = candles([("2026-11-10 00:00", 100, 105, 99, 101), ("2026-11-10 01:00", 101, 103, 95, 96),
                  ("2026-11-10 03:00", 96, 110, 96, 108)])
    hi, lo, close = levels.through_hour(df)
    day = date(2026, 11, 10)
    assert [hi.loc[day, h] for h in (0, 1, 2, 3, 23)] == [105, 105, 105, 110, 110]
    assert [lo.loc[day, h] for h in (0, 1, 2, 3)] == [99, 95, 95, 95]
    assert [close.loc[day, h] for h in (1, 2, 3)] == [96, 96, 108]
    # Where price sits in the range so far, in fifths: after 1:00, 96 is 10% up 95..105 (bin 0);
    # after 3:00, 108 is 87% up 95..110 (bin 4); after 0:00, 101 is 33% up 99..105 (bin 1).
    assert [levels.position(hi, lo, close, h).loc[day] for h in (1, 3, 0)] == [0, 4, 1]


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


def test_nothing_after_the_hour_changes_what_is_known_at_that_hour():
    rows = [("2026-11-10 00:00", 100, 105, 99, 101), ("2026-11-10 01:00", 101, 103, 95, 96)]
    later = [("2026-11-10 05:00", 96, 140, 60, 70)]
    a, b = levels.through_hour(candles(rows)), levels.through_hour(candles(rows + later))
    day = date(2026, 11, 10)
    for h in (0, 1, 4):
        assert [x.loc[day, h] for x in a] == [x.loc[day, h] for x in b]
        assert levels.position(*a, h).loc[day] == levels.position(*b, h).loc[day]


def test_pinball_scores_the_25_50_75_quantile_levels():
    # Past extras 0, 1, 2 ranges: quantiles 0.5 / 1 / 1.5 -> levels 105 / 110 / 115 with a 10-point range.
    past = np.array([0.0, 1.0, 2.0])
    # HOD ends at 110: losses 0.25*(110-105), 0, 0.25*(115-110) -> 1.25 + 0 + 1.25
    assert levels.pinball(110.0, past, 100.0, 1, 10.0) == 2.5
    # LOD mirrored: low 90 from 100, same distances
    assert levels.pinball(90.0, past, 100.0, -1, 10.0) == 2.5


def test_odds_when_no_similar_day_went_further():
    done, lvls = levels.odds(np.array([0.0, 0.0]), 100.0, 1, 10.0)
    assert done == 1.0 and all(np.isnan(lvls))


def test_forecast_line_is_the_median_final_hod_and_lod():
    # Half the days the HOD was already in: the best single guess for the HOD is between "in" and +1 range.
    ex = pd.DataFrame({"up": [0.0, 0.0, 1.0, 2.0], "down": [0.0, 1.0, 1.0, 1.0]})
    f = levels.forecast(ex, high_so_far=200.0, low_so_far=190.0, today_range=10.0)
    assert f["HOD"]["line"] == 205.0 and f["LOD"]["line"] == 180.0
    # Most days already done: the line sits on the high so far ("this is probably the HOD").
    f = levels.forecast(ex.assign(up=[0.0, 0.0, 0.0, 2.0]), 200.0, 190.0, 10.0)
    assert f["HOD"]["line"] == 200.0


def test_day_lines_forecast_each_hour_from_earlier_days_only():
    rows = []
    for d, up in [("2026-11-09", 10), ("2026-11-10", 20), ("2026-11-11", 0)]:  # 11-11 is the target
        rows += [(f"{d} 00:00", 100, 101, 99, 100), (f"{d} 01:00", 100, 100 + up, 99, 100 + up)]
    rows.append(("2026-11-12 00:00", 100, 999, 1, 100))  # a later day must not leak in
    c = candles(rows)
    stats = pd.DataFrame({"open": 100.0, "high": [110.0, 120.0, 101.0, 999.0], "low": 99.0, "r5": 10.0},
                         index=[date(2026, 11, d) for d in (9, 10, 11, 12)])
    out = levels.day_lines(c, stats, date(2026, 11, 11), today_range=10.0)
    assert [r["hour"] for r in out] == [None, 0, 1]
    # Before the open: past HODs were +1 and +2 ranges above the open -> median +1.5 -> 115.
    assert out[0]["HOD"]["line"] == 115.0 and out[0]["n"] == 2
    assert out[2]["high"] == 101 and out[2]["low"] == 99
    # With a 1-day lookback only 11-10 (HOD +2 ranges) counts.
    assert levels.day_lines(c, stats, date(2026, 11, 11), 10.0, lookback_days=1)[0]["HOD"]["line"] == 120.0


def test_heat_counts_where_the_days_that_went_further_ended():
    # Past HODs 1, 1.05 and 3 ranges above the high so far (done days left out), 10-point range, 2-point bins.
    extra = np.array([0.0, 1.0, 1.05, 3.0])
    assert levels.heat(extra, 100.0, 1, 10.0) == [(110.0, 2), (130.0, 1)]
    assert levels.heat(extra, 100.0, -1, 10.0) == [(70.0, 1), (90.0, 2)]  # LOD: below the low so far
    assert levels.heat(extra, 100.0, 1, np.nan) == []


def test_weighted_quantile_with_equal_weights_is_numpys_and_ignores_zero_weights():
    v = np.array([3.0, 1.0, 4.0, 1.5, 9.0])
    q = [0.25, 0.5, 0.75]
    assert np.allclose(levels.wquantile(v, np.ones(5), q), np.quantile(v, q))
    assert np.allclose(levels.wquantile(np.append(v, 99.0), np.append(np.ones(5), 0.0), q), np.quantile(v, q))
    assert levels.wquantile(np.array([7.0]), np.array([1.0]), 0.5) == 7.0


def test_similar_days_weigh_todays_fifth_and_the_nearest_days_equally(monkeypatch):
    monkeypatch.setattr(levels, "K_NEAREST", 2)
    where = np.array([0, 0, 1, 1, 1])
    near = np.array([[0.0, 0.0], [0.1, 0.0], [0.0, 1.0], [5.0, 5.0], [0.05, 0.0]])  # (below high, above low) in yardsticks
    w = levels.similar(where, near, today_where=1, today_near=np.array([0.0, 0.0]))
    # fifth 1: days 2, 3, 4 get 1/3 each; the 2 nearest to (0, 0): days 0 and 4 get 1/2 each
    assert np.allclose(w, [1 / 2, 0, 1 / 3, 1 / 3, 1 / 3 + 1 / 2])


def test_odds_count_each_past_day_by_its_weight():
    done, lvls = levels.odds(np.array([0.0, 1.0, 2.0]), 100.0, 1, 10.0, np.array([2.0, 1.0, 1.0]))
    assert done == 0.5
    assert lvls == levels.odds(np.array([1.0, 2.0]), 100.0, 1, 10.0)[1]


def test_weighted_quantile_uses_every_weight_and_is_symmetric():
    assert levels.wquantile(np.array([0.0, 1.0, 2.0]), np.array([1.0, 1.0, 10.0]), 0.5) > 1.0  # pulled toward the heavy 2
    v, w = np.array([0.0, 1.0, 2.0]), np.array([10.0, 1.0, 1.0])
    assert np.isclose(levels.wquantile(v, w, 0.5), -levels.wquantile(-v, w, 0.5))


def test_walk_forward_and_the_live_view_give_the_same_forecast_for_a_day():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2025-01-01", periods=24 * 330, freq="h", tz="America/New_York")
    close = 6000 + rng.normal(0, 3, len(idx)).cumsum()
    c = pd.DataFrame({"Open": close - rng.normal(0, 1, len(idx)), "Close": close}, index=idx)
    c["High"] = c[["Open", "Close"]].max(axis=1) + rng.uniform(0, 4, len(idx))
    c["Low"] = c[["Open", "Close"]].min(axis=1) - rng.uniform(0, 4, len(idx))
    stats = levels.daily_stats(c).dropna()
    target = stats.index[-1]
    wf = levels.walk_forward(stats, *levels.through_hour(c), warmup=len(stats) - 1).set_index("hour")
    live = levels.day_lines(c, stats, target, stats.r5.iloc[-1])
    for row in live:
        if row["hour"] not in levels.CHECKPOINTS:
            continue
        w = wf.loc["open" if row["hour"] is None else f"{row['hour']}:00"]
        assert np.isclose(row["HOD"]["done"], w.HOD_done_pred) and np.isclose(row["LOD"]["done"], w.LOD_done_pred)
        assert np.isclose(abs(stats.high.iloc[-1] - row["HOD"]["line"]), w.HOD_miss)
    # the same holds with a lookback window
    wf = levels.walk_forward(stats, *levels.through_hour(c), warmup=len(stats) - 1, lookback_days=60).set_index("hour")
    live = levels.day_lines(c, stats, target, stats.r5.iloc[-1], lookback_days=60)
    assert np.isclose(live[0]["HOD"]["done"], wf.loc["open"].HOD_done_pred)
    nine = next(r for r in live if r["hour"] == 9)
    assert np.isclose(abs(stats.high.iloc[-1] - nine["HOD"]["line"]), wf.loc["9:00"].HOD_miss)
    assert nine["n"] <= 60


def test_yardstick_blends_earlier_days_parkinson_volatility_only():
    idx = pd.date_range("2026-01-01", periods=30).date
    park = pd.Series(np.arange(1.0, 31.0), index=idx)
    y = levels.yardstick(park)
    assert y.iloc[:22].isna().all()  # needs 22 earlier days
    p = park.iloc[:24]  # the 25th day sees days 1-24
    want = levels.HAR_SCALE * p.iloc[-1] ** levels.HAR[0] * p.tail(5).mean() ** levels.HAR[1] * p.tail(22).mean() ** levels.HAR[2]
    assert np.isclose(y.iloc[24], want)
    changed = park.copy(); changed.iloc[24] = 1000.0  # the day itself never feeds its own yardstick
    assert np.isclose(levels.yardstick(changed).iloc[24], want)
    # a day missing from stats (an expiry week) gets the same yardstick from the days before it
    target = idx[24]
    assert np.isclose(levels.today_yardstick(pd.DataFrame({"park": park.drop(target)}), target), want)


def test_parkinson_volatility_is_in_points():
    df = candles([("2026-11-10 00:00", 100, 101, 99, 100), ("2026-11-10 01:00", 100, 102, 100, 101)])
    from quantistat import daily_stats
    park = daily_stats(df).park.iloc[0]
    assert np.isclose(park, 100 * np.sqrt((np.log(101 / 99) ** 2 + np.log(102 / 100) ** 2) / (4 * np.log(2))))


def test_brightest_bins_are_the_most_common_ends_nearest_first_on_ties():
    bins = [(110.0, 2), (120.0, 5), (130.0, 5), (140.0, 1), (150.0, 3)]
    assert levels.brightest(bins, now=100.0, top=3) == [(120.0, 5), (130.0, 5), (150.0, 3)]
    assert levels.brightest([], now=100.0) == []


def test_plot_draws_one_line_per_bin_seen_twice_in_points_from_the_open():
    f = {"hour": 9, "high": 105.0, "low": 95.0,
         "HOD": {"done": 0.3, "levels": [107.0, 110.0, 115.0], "line": 108.0, "heat": [(110.0, 4), (120.0, 1), (130.0, 2)]},
         "LOD": {"done": 0.6, "levels": [93.0, 90.0, 85.0], "line": 95.0, "heat": [(90.0, 2)]}}
    fig = levels.plot_heat(f, open_price=100.0, title="t")
    ys = sorted(round(l.get_ydata()[0], 2) for l in fig.axes[0].lines if l.get_linestyle() == "-" and l.get_linewidth() > 1.5)
    assert ys == [-10.0, 10.0, 30.0]  # the 120 bin (one day, under half the brightest) is hidden

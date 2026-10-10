from datetime import date

import numpy as np
import pandas as pd

import bias


def day(o, h, l, c):
    return {"open": o, "high": h, "low": l, "close": c, "bullish": c > o}


def test_rules_use_only_what_is_known_at_midnight():
    idx = [date(2026, 11, 9), date(2026, 11, 10), date(2026, 11, 11)]
    stats = pd.DataFrame([day(100, 110, 90, 105), day(104, 108, 88, 95), day(97, 99, 80, 85)], index=idx)
    globex = pd.Series([102.0, 99.0], index=[date(2026, 11, 10), date(2026, 11, 11)])  # previous 18:00 opens
    r = bias.rules(stats, globex).loc[date(2026, 11, 11)]
    assert r.prev_day == False            # Nov 10 closed down
    assert r.overnight == False           # 97 open < 99 at 18:00
    assert r.close_location == False      # 95 is in the lower half of 88..108
    assert r.discount == True             # 97 open below Nov 10's midpoint 98
    assert r.sweep == True                # Nov 10 took Nov 9's low (88 < 90) and closed back above it
    assert np.isnan(r.turn_of_month)      # Nov 11 is not around a month turn


def test_turn_of_month_calls_last_day_and_first_three():
    idx = [date(2026, 10, 29), date(2026, 10, 30), date(2026, 11, 2), date(2026, 11, 5)]
    stats = pd.DataFrame([day(1, 1, 1, 1)] * 4, index=idx)
    r = bias.rules(stats, pd.Series(dtype=float)).turn_of_month
    assert [v == True for v in r] == [False, True, True, False]


def test_evaluate_freezes_direction_on_discovery_and_scores_out_of_sample():
    idx = pd.date_range("2020-01-01", periods=8, freq="365D").date
    bullish = pd.Series([True, False, True, False, True, False, True, False], index=idx)
    rules = pd.DataFrame({"inverse": ~bullish, "coin": [True] * 8}, index=idx)
    table = bias.evaluate(rules, bullish, split=date(2023, 6, 1)).set_index("rule")
    assert table.loc["inverse", "flipped"] == True
    assert table.loc["inverse", "oos_accuracy"] == 1.0  # flipped, it is always right
    assert table.loc["coin", "oos_accuracy"] == 0.5


def test_markov_rules_fire_only_in_their_two_day_state():
    idx = pd.date_range("2026-11-02", periods=4).date
    stats = pd.DataFrame([day(1, 2, 0, 2), day(2, 3, 0, 1), day(1, 2, 0, 0.5), day(1, 1, 1, 1)], index=idx)
    r = bias.markov_rules(stats)
    assert list(r.columns) == ["markov_bear_bear", "markov_bear_bull", "markov_bull_bear", "markov_bull_bull"]
    assert r.iloc[:2].isna().all().all()            # no two-day history yet
    assert r.iloc[2].markov_bull_bear == 1.0 and r.iloc[2].drop("markov_bull_bear").isna().all()
    assert r.iloc[3].markov_bear_bear == 1.0 and r.iloc[3].drop("markov_bear_bear").isna().all()

import numpy as np
import pandas as pd

import legs


def bars(prices):
    """5m bars from (high, low, close); each opens at the previous close."""
    idx = pd.date_range("2026-11-10 09:00", periods=len(prices), freq="5min", tz="America/New_York")
    opens = [prices[0][2]] + [c for _, _, c in prices[:-1]]
    return pd.DataFrame([(o, h, l, c) for o, (h, l, c) in zip(opens, prices)], index=idx,
                        columns=["Open", "High", "Low", "Close"])


# up from 100 to 110, pulls back 3 (not a leg of 5), up to 112, down to 106 (turn at 112), down to 104,
# back up to 109 (turn at 104)
PATH = [(101, 100, 101), (105, 101, 105), (110, 105, 110), (110, 107, 107), (112, 107, 112),
        (112, 108, 108), (108, 106, 106), (106, 104, 105), (109, 105, 109)]


def test_zigzag_turns_only_after_a_whole_leg_against_the_extreme():
    day = legs.legs(bars(PATH), theta=5.0)
    assert day.dir.tolist() == [0, 1, 1, 1, 1, 1, -1, -1, 1]
    assert day.start.tolist()[1:] == [100, 100, 100, 100, 100, 112, 112, 104]
    assert day.ext.tolist()[1:] == [105, 110, 110, 112, 112, 106, 104, 109]
    assert day.age.tolist()[1:] == [0, 0, 1, 0, 1, 0, 0, 0]


def test_ended_marks_the_bars_whose_extreme_was_the_legs_end_and_skips_the_unfinished_leg():
    day = legs.legs(bars(PATH), theta=5.0)
    # up leg 100 -> 112: only after 112 is printed is its extreme the end; the last leg (from 104) never turned
    assert day.ended.tolist()[1:6] == [0, 0, 0, 1, 1]
    assert day.ended.tolist()[6:8] == [0, 1]
    assert np.isnan(day.ended.iloc[0]) and np.isnan(day.ended.iloc[-1])


def test_retrace_and_size_are_in_legs():
    day = legs.legs(bars(PATH), theta=5.0)
    assert day.r.iloc[3] == 0.6 and day.g.iloc[3] == 2.0  # 110 -> 107 is 3/5 back; 100 -> 110 is 2 legs
    assert day.r.iloc[5] == 0.8 and day.g.iloc[5] == 2.4


def test_nothing_after_a_bar_changes_what_is_known_at_that_bar():
    a, b = legs.legs(bars(PATH[:5]), 5.0), legs.legs(bars(PATH), 5.0)
    cols = ["dir", "start", "ext", "age", "r", "g"]
    pd.testing.assert_frame_equal(a[cols], b[cols].iloc[:5])
    assert np.allclose(legs.features(a), legs.features(b.iloc[:5]), equal_nan=True)  # NaN: no leg yet


def test_a_wrong_call_is_stopped_just_past_the_extreme():
    day = legs.legs(bars(PATH), 5.0)
    p = np.where(np.arange(len(day)) == 3, 0.9, 0.0)  # at 107 the model calls the end of the up leg at 110
    t = legs.trades(day, p, 5.0, cutoff=0.5)
    assert [(x["side"], x["entry"], x["exit"]) for x in t] == [(-1, 107, 110.25)]
    assert t[0]["points"] == -3.25 - legs.COST


def test_a_right_call_rides_the_new_leg_until_the_model_calls_its_end_and_flips():
    day = legs.legs(bars(PATH), 5.0)
    p = np.where(np.isin(np.arange(len(day)), [5, 7]), 0.9, 0.0)  # sell 108 at the top, cover 105 at the bottom
    t = legs.trades(day, p, 5.0, cutoff=0.5)
    assert [(x["side"], x["entry"], x["exit"]) for x in t][:2] == [(-1, 108, 105), (1, 105, 109)]  # last: day end


def test_random_walk_odds_are_the_share_of_the_leg_already_given_back():
    # driftless walk between the extreme (dist r legs above) and the turn (1 - r below): hits the turn first with odds r
    assert legs.rw_end(np.array([0.0, 0.25, 0.9])).tolist() == [0.01, 0.25, 0.9]


def test_each_bar_uses_its_own_leg_size():
    theta = np.array([5.0] * 6 + [7.0] * 3)  # a bigger day from bar 6: 112 -> 106 is no longer a turn, 104 is
    day = legs.legs(bars(PATH), theta)
    assert day.dir.tolist()[6:] == [1, -1, -1] and day.ext.tolist()[6:] == [112, 104, 104]

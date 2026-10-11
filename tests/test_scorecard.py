from datetime import date

import numpy as np
import pandas as pd

import scorecard as sc


def test_bright_lines_are_the_most_crowded_1_point_cells():
    assert sc.bright_lines(np.array([5.2, 4.9, 5.1, 10.0, 10.2, 20.0, 30.0]), top=2).tolist() == [5.0, 10.0]


def test_pinball_scores_the_25_50_75_quantiles():
    # Sample 0, 10, 20 -> quantiles 5, 10, 15; actual 10 -> 0.25*5 + 0 + 0.25*5
    assert sc.pinball(10.0, np.array([0.0, 10.0, 20.0])) == 2.5


def test_each_day_is_scored_from_earlier_days_only():
    days = [date(2026, 1, 5), date(2026, 2, 5), date(2026, 3, 5), date(2026, 4, 5)]
    stats = pd.DataFrame({"open": 100.0, "high": [110.0, 110.0, 110.0, 999.0], "low": [90.0, 90.0, 90.0, 1.0],
                          "bullish": True, "r5": 10.0}, index=days)
    methods = {"all days, raw": (lambda d, past: np.full(len(past), True), None)}
    rows = sc.scorecard(stats, methods, start=date(2026, 3, 1)).set_index("day")
    # 3-05 sees two +10/-10 days: its own +10/-10 is right on the bright line, the pinball loss is 0.
    first = rows.loc[date(2026, 3, 5)]
    assert (first.HOD_hit, first.LOD_hit, first.HOD_pinball, first.LOD_pinball) == (True, True, 0.0, 0.0)
    # 4-05 (the +899 day) does not leak into 3-05, and is itself far off.
    assert rows.loc[date(2026, 4, 5)].HOD_hit == False

from datetime import date

import numpy as np
import pandas as pd

import journal


def test_call_is_right_when_the_more_likely_side_happened():
    rows = pd.DataFrame({"HOD_done_pred": [0.7, 0.3, 0.6], "HOD_done_real": [1.0, 1.0, 0.0],
                         "LOD_done_pred": [0.2, 0.2, 0.5], "LOD_done_real": [0.0, 1.0, 1.0],
                         **{f"{s}_{p}": [None] * 3 for s in ("HOD", "LOD") for p in (75, 25)}})
    out = journal.add_verdicts(rows)
    assert out.HOD_call_right.tolist() == [True, False, False]
    assert out.LOD_call_right.tolist() == [True, False, True]


def test_append_replaces_a_rescored_day(tmp_path):
    path = tmp_path / "journal.csv"
    day = lambda d, x: pd.DataFrame({"day": [d, d], "hour": ["open", "9:00"], "x": [x, x]})
    journal.append(path, day(date(2026, 10, 8), 1))
    journal.append(path, day(date(2026, 10, 9), 2))
    journal.append(path, day(date(2026, 10, 8), 3))  # re-run of 10-08
    saved = pd.read_csv(path)
    assert saved.day.tolist() == ["2026-10-08", "2026-10-08", "2026-10-09", "2026-10-09"]
    assert saved.x.tolist() == [3, 3, 2, 2]


def test_in_band_means_the_real_hod_lod_landed_between_the_75_and_25_percent_levels():
    rows = pd.DataFrame({"HOD_done_pred": [0.1] * 4, "HOD_done_real": [0.0] * 3 + [1.0],
                         "HOD_75": [1.0, 1.0, 0.0, None], "HOD_25": [0.0, 1.0, 0.0, None],
                         "LOD_done_pred": [0.1] * 4, "LOD_done_real": [0.0] * 4,
                         "LOD_75": [1.0] * 4, "LOD_25": [0.0] * 4})
    out = journal.add_verdicts(rows)
    assert out.HOD_in_band.tolist()[:3] == [1.0, 0.0, 0.0]  # inside, beyond the 25% level, short of the 75%
    assert pd.isna(out.HOD_in_band.iloc[3])                       # high already in: no band to land in
    assert out.LOD_in_band.all()


def test_a_range_scores_each_day_exactly_as_scoring_it_alone(monkeypatch):
    monkeypatch.setattr(journal, "use_implied", lambda stats: None)  # keep the 5-day range, no download
    rng = np.random.default_rng(0)
    idx = pd.date_range("2026-10-01", "2026-11-28 23:00", freq="h", tz="America/New_York")
    close = 6000 + rng.normal(0, 3, len(idx)).cumsum()
    candles = pd.DataFrame({"Open": close - rng.normal(0, 1, len(idx)), "Close": close}, index=idx)
    candles["High"] = candles[["Open", "Close"]].max(axis=1) + rng.uniform(0, 4, len(idx))
    candles["Low"] = candles[["Open", "Close"]].min(axis=1) - rng.uniform(0, 4, len(idx))
    days = [date(2026, 11, d) for d in (20, 21, 22)]
    together = journal.score_days(candles, days[0], days[-1])
    alone = pd.concat([journal.score_days(candles, d, d) for d in days])
    key = ["day", "hour"]
    pd.testing.assert_frame_equal(together.sort_values(key).reset_index(drop=True),
                                  alone.sort_values(key).reset_index(drop=True))
    assert sorted(set(together.day)) == days

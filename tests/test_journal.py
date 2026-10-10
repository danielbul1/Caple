from datetime import date

import pandas as pd

import journal


def test_call_is_right_when_the_more_likely_side_happened():
    rows = pd.DataFrame({"HOD_done_pred": [0.7, 0.3, 0.6], "HOD_done_real": [1.0, 1.0, 0.0],
                         "LOD_done_pred": [0.2, 0.2, 0.5], "LOD_done_real": [0.0, 1.0, 1.0]})
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

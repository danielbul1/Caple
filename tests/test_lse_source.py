import lse_source as lse


def test_to_frame_converts_utc_rows_to_new_york_candles():
    rows = [{"ts": "2016-05-29 22:00:00.000000", "symbol": "ES.F", "open": 2091.5, "high": 2093,
             "low": 2091.25, "close": 2092.25, "volume": 107}]
    df = lse.to_frame(rows)
    assert str(df.index[0]) == "2016-05-29 18:00:00-04:00"  # Sunday 18:00 New York reopen
    assert df.iloc[0].to_dict() == {"Open": 2091.5, "High": 2093, "Low": 2091.25, "Close": 2092.25, "Volume": 107}


def test_cache_round_trips_across_a_daylight_saving_change(tmp_path):
    df = lse.to_frame([{"ts": ts, "open": 1, "high": 2, "low": 0, "close": 1, "volume": 5}
                       for ts in ("2025-11-01 12:00:00", "2025-11-03 12:00:00")])  # EDT, then EST
    df.to_csv(tmp_path / "c.csv")
    assert lse.read_cache(tmp_path / "c.csv").index.equals(df.index)


def test_event_labels_use_the_new_york_date_and_prefer_fomc():
    rows = [{"event": "Fed Interest Rate Decision", "datetime": "2026-12-09 19:00:00"},
            {"event": "Core Inflation Rate MoM", "datetime": "2026-12-09 13:30:00"},
            {"event": "Core Inflation Rate MoM NOV", "datetime": "2026-11-13 01:30:00"},  # 20:30 NY on the 12th
            {"event": "Core Inflation Rate MoM Final DEC", "datetime": "2024-02-09 14:30:00"}]  # seasonal revision
    from datetime import date
    assert lse.event_labels(rows) == {date(2026, 12, 9): "FOMC", date(2026, 11, 12): "CPI"}

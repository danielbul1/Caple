from datetime import date

import numpy as np
import pandas as pd

import app
import lse_source


def walk(days: int, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-01-01", periods=24 * days, freq="h", tz="America/New_York")
    close = 6000 + rng.normal(0, 3, len(idx)).cumsum()
    c = pd.DataFrame({"Open": close - rng.normal(0, 1, len(idx)), "Close": close, "Volume": 1.0}, index=idx)
    c["High"] = c[["Open", "Close"]].max(axis=1) + rng.uniform(0, 4, len(idx))
    c["Low"] = c[["Open", "Close"]].min(axis=1) - rng.uniform(0, 4, len(idx))
    return c


def serve(monkeypatch, candles, today=date(2026, 1, 1)):
    monkeypatch.setattr(app, "_live", None)
    monkeypatch.setattr(app, "today_market", lambda: today)
    monkeypatch.setattr(lse_source, "fetch", lambda: candles)
    return app.app.test_client()


END, TARGET = "2025-03-20", date(2025, 3, 21)  # the End Date is the day before the forecast day


def test_cells_are_one_point_from_the_open_and_hide_single_days(monkeypatch):
    data = serve(monkeypatch, walk(90)).get(f"/api/price-based?end={END}&at=open").get_json()
    assert data["date"] == TARGET.isoformat() and data["hour"] is None
    assert data["high"] == data["low"] == data["open"]
    cells = data["cells"]
    assert cells and all(c["days"] >= 2 for c in cells)
    assert all(float(c["points"]).is_integer() for c in cells)
    assert all((c["side"] == "HOD") == (c["points"] > 0) for c in cells)
    assert sum(c["days"] for c in cells if c["side"] == "HOD") <= data["n"]


def test_nothing_after_the_picked_hour_changes_the_answer_for_that_hour(monkeypatch):
    full = walk(90)
    cut = full[full.index <= pd.Timestamp(f"{TARGET} 05:00", tz="America/New_York")]
    keys = ["date", "hour", "open", "high", "low", "n", "cells"]
    a = serve(monkeypatch, cut).get(f"/api/price-based?end={END}&at=5").get_json()
    b = serve(monkeypatch, full).get(f"/api/price-based?end={END}&at=5").get_json()
    assert a["hour"] == 5 and {k: a[k] for k in keys} == {k: b[k] for k in keys}
    assert a["high"] > a["open"] > a["low"]


def test_live_today_answers_after_the_latest_candle(monkeypatch):
    full = walk(90)
    cut = full[full.index <= pd.Timestamp(f"{TARGET} 07:00", tz="America/New_York")]
    data = serve(monkeypatch, cut, today=TARGET).get(f"/api/price-based?end={END}").get_json()
    assert data["live"] and data["hour"] == 7 and data["hours"] == list(range(8))
    assert not serve(monkeypatch, full).get(f"/api/price-based?end={END}").get_json()["live"]


def test_bad_requests(monkeypatch):
    client = serve(monkeypatch, walk(90))
    assert client.get("/api/price-based?end=nope").status_code == 400
    latest = client.get("/api/price-based").get_json()  # no End Date: the latest day
    assert latest["date"] == "2025-04-01" and latest["end"] == "2025-03-31"  # DST spills one candle into 04-01
    assert client.get(f"/api/price-based?end={END}&at=24").status_code == 400
    assert client.get("/api/price-based?end=2026-01-01").status_code == 404  # no day after it yet

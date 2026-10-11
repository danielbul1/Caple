from datetime import date

import numpy as np
import pandas as pd
import pytest

import app
import quantistat
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
    assert data["min_days"] == 2


def test_the_end_date_stays_the_one_picked(monkeypatch):
    # 03-20 is like a Sunday: only evening bars, no 00:00 open, so the day after 03-19 is 03-21.
    full = walk(90)
    sunday = (full.index.date == date(2025, 3, 20)) & (full.index.hour < 18)
    data = serve(monkeypatch, full[~sunday]).get("/api/price-based?end=2025-03-19&at=open").get_json()
    assert data["date"] == TARGET.isoformat() and data["end"] == "2025-03-19"


@pytest.mark.parametrize("at, last, live", [("open", 0, False), ("5", 5, False), ("", 5, True)])
def test_nothing_after_the_picked_time_changes_the_answer_for_that_time(monkeypatch, at, last, live):
    # Before the open, after an hour, and live (the latest candle is 05:00): the same answer as
    # the full history asked for that time.
    full = walk(90)
    cut = full[full.index <= pd.Timestamp(f"{TARGET} {last:02}:00", tz="America/New_York")].copy()
    if at == "open":  # before the open only the 00:00 Open is known, not how that candle went
        cut.iloc[-1, cut.columns.get_indexer(["High", "Low", "Close"])] += [50, -50, 20]
    keys = ["date", "hour", "open", "high", "low", "n", "cells"]
    a = serve(monkeypatch, cut, today=TARGET if live else date(2026, 1, 1)).get(f"/api/price-based?end={END}" + (at and f"&at={at}")).get_json()
    b = serve(monkeypatch, full).get(f"/api/price-based?end={END}&at={at or last}").get_json()
    assert a["live"] == live and {k: a[k] for k in keys} == {k: b[k] for k in keys}
    assert (a["high"] > a["open"] > a["low"]) == (at != "open")


def test_live_today_answers_after_the_latest_candle(monkeypatch):
    full = walk(90)
    cut = full[full.index <= pd.Timestamp(f"{TARGET} 07:00", tz="America/New_York")]
    data = serve(monkeypatch, cut, today=TARGET).get(f"/api/price-based?end={END}").get_json()
    assert data["live"] and data["hour"] == 7 and data["hours"] == list(range(8))
    assert not serve(monkeypatch, full).get(f"/api/price-based?end={END}").get_json()["live"]


def test_no_end_date_answers_for_the_latest_day(monkeypatch):
    latest = serve(monkeypatch, walk(90)).get("/api/price-based").get_json()
    assert latest["date"] == "2025-04-01" and latest["end"] == "2025-03-31"  # DST spills one candle into 04-01


def test_bad_requests_are_refused(monkeypatch):
    client = serve(monkeypatch, walk(90))
    assert client.get("/api/price-based?end=nope").status_code == 400
    assert client.get(f"/api/price-based?end={END}&at=24").status_code == 400
    assert client.get("/api/price-based?end=2026-01-01").status_code == 404  # no day after it yet
    assert client.get("/api/price-based?end=2000-01-01").status_code == 404  # no history before it


def two_levels() -> pd.DataFrame:
    """120 days of the same shape, at a price level of 3000 for the first 40 days and 6000 after:
    the same day in yardsticks, half the points (HOD +12.6 / LOD -9.6 at 3000, +25.2 / -19.2 at 6000)."""
    idx = pd.date_range("2025-01-01", periods=24 * 120, freq="h", tz="America/New_York")
    shape = 1 + 0.001 * np.array([0, 1, 2, 3, 4, 3, 2, 1, 0, -1, -2, -3] * 2)
    level = np.where(np.arange(len(idx)) < 24 * 40, 3000.0, 6000.0)
    c = pd.DataFrame({"Open": level * np.r_[1, shape[:-1]][idx.hour], "Close": level * shape[idx.hour], "Volume": 1.0}, index=idx)
    c["High"] = c[["Open", "Close"]].max(axis=1) + level * 0.0002
    c["Low"] = c[["Open", "Close"]].min(axis=1) - level * 0.0002
    return c


def test_default_mode_compares_days_in_yardsticks_and_quantistat_mode_in_raw_points(monkeypatch):
    client = serve(monkeypatch, two_levels())
    hod = lambda q: {c["points"] for c in client.get(f"/api/price-based?end=2025-04-24&at=open{q}").get_json()["cells"] if c["side"] == "HOD"}
    assert min(hod("")) >= 25  # the days at 3000 count as the same +25 day at today's 6000
    assert {13, 25} <= hod("&mode=quantistat&period=max")  # the days at 3000 stay at their raw +13


def test_the_period_counts_back_from_the_end_date(monkeypatch):
    full, q = walk(400), "/api/price-based?end=2025-12-10&at=open&mode=quantistat"
    a = serve(monkeypatch, full).get(f"{q}&period=3mo").get_json()
    later = serve(monkeypatch, full, today=date(2030, 6, 1)).get(f"{q}&period=3mo").get_json()
    stats = quantistat.daily_stats(full)
    window = [date(2025, 9, 11) <= d <= date(2025, 12, 10) for d in stats.index]  # 3 months up to 12-10
    assert a["mode"] == "quantistat" and a["period"] == "3mo"
    assert a["cells"] == later["cells"] and a["n"] == later["n"] == sum(window)
    assert serve(monkeypatch, full).get(f"{q}&period=6mo").get_json()["n"] > a["n"]
    assert serve(monkeypatch, full).get(q).get_json()["period"] == "2y"


def test_quantistat_mode_only_answers_before_the_open(monkeypatch):
    client = serve(monkeypatch, walk(90))
    assert client.get(f"/api/price-based?end={END}&at=open&mode=quantistat").status_code == 200
    assert client.get(f"/api/price-based?end={END}&at=5&mode=quantistat").status_code == 400
    assert client.get(f"/api/price-based?end={END}&mode=quantistat").status_code == 400  # latest candle / live
    assert client.get(f"/api/price-based?end={END}&at=open&mode=quantistat&period=5y").status_code == 400
    assert client.get(f"/api/price-based?end={END}&at=open&mode=nope").status_code == 400
    assert client.get(f"/api/price-based?end={END}&at=open&period=5y").status_code == 200  # no Period outside the mode


def test_quantistat_mode_uses_the_same_days_as_the_default_mode(monkeypatch):
    client = serve(monkeypatch, walk(90))
    default = client.get(f"/api/price-based?end={END}&at=open").get_json()
    raw = client.get(f"/api/price-based?end={END}&at=open&mode=quantistat&period=max").get_json()
    assert raw["n"] == default["n"]  # the warm-up days without an expected range stay out in both

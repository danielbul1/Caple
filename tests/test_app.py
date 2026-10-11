from datetime import date, timedelta

import pandas as pd

import app
import lse_source


def bars(start, n, price):
    idx = pd.date_range(start, periods=n, freq="h", tz="America/New_York")
    return pd.DataFrame({c: float(price) for c in ("Open", "High", "Low", "Close", "Volume")}, index=idx)


def test_candles_serve_the_lookback_before_the_picked_date_from_lse(monkeypatch):
    monkeypatch.setattr(app, "_live", None)
    monkeypatch.setattr(app, "today_market", lambda: date(2018, 6, 5))
    monkeypatch.setattr(lse_source, "fetch", lambda: bars("2016-06-01 00:00", 24 * 800, 1))
    client = app.app.test_client()
    days = client.get("/api/available-dates").get_json()["available"]
    assert days[0] == (date(2016, 6, 1) + timedelta(days=app.LOOKBACK_DAYS)).isoformat() and days[-1] == "2018-06-05"
    data = client.get("/api/candles?date=2018-06-05").get_json()
    assert data["first"] == "2016-06-06 00:00" and data["last"] == "2018-06-04 23:00"
    assert client.get("/api/candles?date=2016-07-01").status_code == 422  # not enough history before it


def test_the_page_is_caple_with_its_tiles():
    page = app.app.test_client().get("/").get_data(as_text=True)
    assert "Caple" in page
    for tile in ("Price Based", "Time Based", "Level Validator", "Seasonal", "Intraday"):
        assert f">{tile}</button>" in page

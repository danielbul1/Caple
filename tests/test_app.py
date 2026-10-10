import pandas as pd

import app
import levels
import lse_source


def bars(start, n, price):
    idx = pd.date_range(start, periods=n, freq="h", tz="America/New_York")
    return pd.DataFrame({c: float(price) for c in ("Open", "High", "Low", "Close", "Volume")}, index=idx)


def test_live_candles_use_lse_history_topped_up_with_yahoos_newest_bars(monkeypatch):
    monkeypatch.setenv("LSE_API_KEY", "x")
    monkeypatch.setattr(app, "_live", None)
    monkeypatch.setattr(levels, "implied_closes", lambda: pd.Series(dtype=float))
    monkeypatch.setattr(lse_source, "fetch", lambda: bars("2016-06-01 00:00", 3, 1))
    monkeypatch.setattr(app, "download", lambda start, end: bars("2016-06-01 01:00", 4, 2))  # overlaps 01:00, 02:00
    candles, _ = app.live_candles()
    assert candles.Close.tolist() == [1, 1, 1, 2, 2]  # LSE wherever it has the bar, Yahoo only after it
    assert candles.index.is_monotonic_increasing

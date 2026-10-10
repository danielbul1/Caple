import numpy as np
import pandas as pd

import forecast_bias as fb


def candles(n=300, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2014-01-01", periods=n)
    close = 1000 + rng.normal(0, 5, n).cumsum()
    open_ = close + rng.normal(0, 3, n)
    return pd.DataFrame({"Open": open_, "High": np.maximum(open_, close) + 2, "Low": np.minimum(open_, close) - 2,
                         "Close": close, "VIX": 15 + rng.normal(0, 1, n)}, index=idx)


def test_features_use_only_earlier_sessions():
    df = candles()
    changed = df.copy()
    changed.iloc[-1] = changed.iloc[-1] * 1.1  # today's prices and VIX close are not known at its open
    a, b = fb.features(df), fb.features(changed)
    assert a[fb.FEATURES].equals(b[fb.FEATURES])
    assert a.month_start.loc["2014-02-03"] == 1 and a.month_start.loc["2014-02-04"] == 0


def test_markov_counts_what_followed_each_state_in_training():
    idx = pd.bdate_range("2020-01-01", periods=8)
    bull = [True, False, True, False, True, False, True, True]  # training: after bull 0 of 3, after bear 2 of 2
    data = pd.DataFrame({"bullish": bull, "range_ratio": 1.0}, index=idx)
    p = fb.markov(data.iloc[:6], data.iloc[6:], 1)
    assert np.allclose(p, [(2 + 0.5) / 3, (0 + 0.5) / 4])  # day 6 follows a bear day, day 7 a bull day


def test_walk_forward_trains_only_on_earlier_years_and_scores_against_base_rate():
    idx = pd.bdate_range("2014-01-01", "2017-12-31")
    data = pd.DataFrame({"bullish": np.arange(len(idx)) % 3 > 0}, index=idx)
    seen = []
    spy = lambda train, test: seen.append(train.index.max() < test.index.min()) or np.full(len(test), 0.9)
    preds = fb.walk_forward(data, {"spy": spy}, first_year=2016)
    assert seen == [True, True] and preds.index.year.min() == 2016
    table = fb.score(preds).set_index("model")
    assert table.loc["spy", "accuracy"] == table.loc["spy", "base_accuracy"]  # both call bullish every day
    assert table.loc["spy", "brier_edge_x1e4"] < 0  # 0.9 is overconfident for a 2/3 rate


def test_sarimax_forecasts_do_not_see_the_future():
    data = fb.features(candles(400))
    train, test = data.iloc[:300], data.iloc[300:]
    p = fb.sarimax(train, test)
    later = test.copy()
    later.loc[later.index[-1], "ret"] = 0.5
    assert len(p) == len(test) and ((p > 0) & (p < 1)).all()
    assert np.allclose(p, fb.sarimax(train, later))  # a session's own return never feeds its forecast

"""Can anything forecast ES's daily direction? Walk-forward test of the Discord
"statistical data" ideas (markov-process, sarimax, bias-forecasting).

Each LSE calendar day of ES (00:00-23:00 NY, since mid 2016, the days quantistat.py
keeps) is called bullish (close > open) or not from earlier days only. Every model is
refit at the start of each year on all earlier days, gives P(bullish) for every day of
that year, and is scored on 2019 onward against the base rate (share of bullish days
before that year):
- Brier score (primary, pre-registered): edge = base Brier - model Brier per day; a
  model passes only if the mean edge is more than two standard errors above 0.
- accuracy of calling the likelier side, against always calling the base-rate side.

Models:
- markov1/2/3: share of bullish days after the same last 1/2/3 directions
- markov2_range: same, the state also says whether each day's range was above its
  20-day average (big/small days)
- sarimax: SARIMAX(1,0,1)x(1,0,1,5) on the day's return with the range ratio as an
  exogenous input; P = chance the one-step forecast is above 0
- logit: logistic regression on the features below
- gbm: gradient-boosted trees (sklearn's LightGBM-style HistGradientBoosting)

Run: python forecast_bias.py
"""

import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app import today_market
from quantistat import daily_stats, load_candles

FIRST_TEST_YEAR = 2019
FEATURES = ["ret1", "ret2", "ret5", "range_ratio", "close_loc", "ma20_dist", "weekday", "month_start"]


def load() -> pd.DataFrame:
    stats = daily_stats(load_candles())
    stats = stats[stats.index < today_market()]  # today is not finished
    stats.index = pd.to_datetime(stats.index)
    return stats.rename(columns=str.capitalize)[["Open", "High", "Low", "Close"]]


def features(df: pd.DataFrame) -> pd.DataFrame:
    """One row per day, built only from the days before it."""
    ret = df.Close / df.Open - 1
    rng = (df.High - df.Low) / df.Close
    p = lambda s: s.shift(1)
    out = pd.DataFrame({
        "bullish": df.Close > df.Open,
        "ret": ret,
        "ret1": p(ret),
        "ret2": p(ret).rolling(2).sum(),
        "ret5": p(ret).rolling(5).sum(),
        "range_ratio": p(rng / rng.rolling(20).mean()),
        "close_loc": p((df.Close - df.Low) / (df.High - df.Low)),
        "ma20_dist": p(df.Close / df.Close.rolling(20).mean() - 1),
        "weekday": df.index.weekday,
        "month_start": (df.index.month != df.index.to_series().shift().dt.month).astype(float),
    }, index=df.index)
    return out.dropna()


def markov(train: pd.DataFrame, test: pd.DataFrame, order: int, with_range: bool = False) -> np.ndarray:
    """Laplace-smoothed share of bullish days after the same state in training."""
    both = pd.concat([train, test])
    bits = [both.bullish.shift(k) for k in range(1, order + 1)]
    if with_range:  # range_ratio is already yesterday's, so day t-k's is shift(k - 1)
        bits += [both.range_ratio.shift(k - 1) > 1 for k in range(1, order + 1)]
    state = sum(b.astype(float) * 2 ** i for i, b in enumerate(bits))
    s_train, s_test = state.loc[train.index], state.loc[test.index]
    counts = train.bullish.groupby(s_train).agg(["sum", "count"])
    prior = train.bullish.mean()
    p = (counts["sum"] + prior) / (counts["count"] + 1)
    return s_test.map(p).fillna(prior).to_numpy()


def sarimax(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Fit on training, then filter through the test year with those parameters: each
    one-step forecast uses only earlier days."""
    exog = ["range_ratio"]
    spec = dict(order=(1, 0, 1), seasonal_order=(1, 0, 1, 5), trend="c")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        params = SARIMAX(train.ret, train[exog], **spec).fit(disp=False).params
        both = pd.concat([train, test])
        pred = SARIMAX(both.ret.to_numpy(), both[exog].to_numpy(), **spec).filter(params).get_prediction()
    mean, sd = pred.predicted_mean[-len(test):], np.sqrt(pred.var_pred_mean[-len(test):])
    return norm.cdf(mean / sd)


def classifier(model):
    def fit_predict(train, test):
        return model.fit(train[FEATURES], train.bullish).predict_proba(test[FEATURES])[:, 1]
    return fit_predict


MODELS = {
    "markov1": lambda tr, te: markov(tr, te, 1),
    "markov2": lambda tr, te: markov(tr, te, 2),
    "markov3": lambda tr, te: markov(tr, te, 3),
    "markov2_range": lambda tr, te: markov(tr, te, 2, with_range=True),
    "sarimax": sarimax,
    "logit": classifier(make_pipeline(StandardScaler(), LogisticRegression(C=0.1))),
    "gbm": classifier(HistGradientBoostingClassifier(max_depth=3, learning_rate=0.03, max_iter=150,
                                                     min_samples_leaf=100, random_state=0)),
}


def walk_forward(data: pd.DataFrame, models: dict, first_year: int = FIRST_TEST_YEAR) -> pd.DataFrame:
    """P(bullish) per test day: refit each January on every earlier day."""
    years = data.index.year
    out = []
    for year in range(first_year, years.max() + 1):
        train, test = data[years < year], data[years == year]
        if len(test):
            row = {name: fit(train, test) for name, fit in models.items()}
            out.append(pd.DataFrame({"bullish": test.bullish, "base": train.bullish.mean(), **row}, index=test.index))
    return pd.concat(out)


def score(preds: pd.DataFrame) -> pd.DataFrame:
    y = preds.bullish.astype(float)
    base_brier = (preds.base - y) ** 2
    base_right = (preds.base >= 0.5) == preds.bullish
    rows = []
    for name in preds.columns.drop(["bullish", "base"]):
        edge = base_brier - (preds[name] - y) ** 2
        right = (preds[name] >= 0.5) == preds.bullish
        rows.append({"model": name, "brier_edge_x1e4": edge.mean() * 1e4, "two_se_x1e4": 2 * edge.sem() * 1e4,
                     "accuracy": right.mean(), "base_accuracy": base_right.mean(),
                     "calls_bearish": (preds[name] < 0.5).mean(), "passed": edge.mean() > 2 * edge.sem()})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    data = features(load())
    preds = walk_forward(data, MODELS)
    print(f"{len(data)} days {data.index[0]:%Y-%m-%d} .. {data.index[-1]:%Y-%m-%d}, scored "
          f"{len(preds)} from {FIRST_TEST_YEAR}, bullish {preds.bullish.mean():.1%}\n")
    print(score(preds).round(4).to_string(index=False))
    halves = preds.index.year < 2023
    for label, part in [("2019-2022", preds[halves]), ("2023-", preds[~halves])]:
        print(f"\n{label}\n" + score(part)[["model", "brier_edge_x1e4", "two_se_x1e4", "accuracy", "base_accuracy"]].round(4).to_string(index=False))

"""Score every day: were the levels right? Which way of building them is best?

Each day from START on, before its 00:00 open, every method builds the HOD and LOD
distances from the open out of earlier days only, and is scored against what happened:

- pinball: quantile loss of the 25/50/75% levels, in points (one proper score for the
  whole forecast; lower is better).
- reached_75/50/25: did the day reach the level that 75/50/25% of the sample reached?
  Honest levels hit about that often.
- hit: the day's HOD (LOD) landed within TOLERANCE points of one of the TOP brightest
  1-point lines of the QuantiStat heatmap. hit_random is the same lines against another
  random day's HOD (LOD): if hit is no higher, the bright lines know nothing about the day.

Methods: the sample (same day of month, same weekday, or all days), raw points or rescaled
to today's volatility (prior 5-day range r5), and the bias (bullish = closed above the open) either unknown
or known: "bias known" peeks at the day's real close, the upper bound of picking the
bias by hand. Every per-day row goes to scorecard.csv.

Run: python scorecard.py [DATE ...]   (dates: print every method's call that day)
"""

import sys
from datetime import date

import numpy as np
import pandas as pd

from quantistat import daily_stats, load_candles

START = date(2018, 1, 1)
QUANTILES = [0.25, 0.5, 0.75]
TOP, TOLERANCE = 3, 3.0


def bright_lines(distances: np.ndarray, top: int = TOP) -> np.ndarray:
    """The `top` most crowded 1-point cells (QuantiStat's brightest), closest to 0 on ties."""
    values, counts = np.unique(np.round(distances), return_counts=True)
    order = np.lexsort((np.abs(values), -counts))
    return np.sort(values[order[:top]])


def pinball(actual: float, sample: np.ndarray) -> float:
    return sum(max(q * (actual - x), (q - 1) * (actual - x)) for q, x in zip(QUANTILES, np.quantile(sample, QUANTILES)))


def scorecard(stats: pd.DataFrame, methods: dict, start: date = START) -> pd.DataFrame:
    """methods: name -> (pick(day, past) -> bool mask over past, scale column or None for raw points)."""
    up, down = (stats.high - stats.open).to_numpy(), (stats.open - stats.low).to_numpy()
    rows = []
    for i in np.flatnonzero(stats.index >= start):
        day, past = stats.index[i], stats.iloc[:i]
        for name, (pick, scale) in methods.items():
            mask = pick(day, past) & (True if scale is None else past[scale].notna().to_numpy())
            unit = 1.0 if scale is None else stats[scale].iloc[i]
            k = 1.0 if scale is None else unit / past[scale][mask].to_numpy()
            row = {"day": day, "method": name, "n": int(mask.sum()), "unit": unit, "bullish": bool(stats.bullish.iloc[i])}
            if row["n"] < 2 or np.isnan(unit):
                continue
            for side, dist in (("HOD", up), ("LOD", down)):
                sample, actual = dist[:i][mask] * k, dist[i]
                lines = bright_lines(sample)
                row |= {f"{side}_actual": actual, f"{side}_lines": lines,
                        f"{side}_levels": np.quantile(sample, QUANTILES).round(1),
                        f"{side}_hit": bool(np.abs(lines - actual).min() <= TOLERANCE),
                        f"{side}_pinball": pinball(actual, sample),
                        **{f"{side}_reached_{int(100 - q * 100)}": bool(actual >= x)
                           for q, x in zip(QUANTILES, np.quantile(sample, QUANTILES))}}
            rows.append(row)
    return pd.DataFrame(rows)


def random_hits(result: pd.DataFrame, seed: int = 0) -> pd.Series:
    """Share of each method's bright lines hit by another random scored day's HOD/LOD,
    moved into that day's units (another day's 40 points on a calm day is more on a wild one).
    For "bias known" methods the other day has the same bias, or the baseline would only
    measure the bias, not the lines."""
    rng = np.random.default_rng(seed)
    out = {}
    for name, g in result.groupby("method"):
        g = g.reset_index(drop=True)
        groups = g.groupby("bullish").groups.values() if name.endswith("bias known") else [g.index]
        j = np.empty(len(g), int)
        for idx in groups:
            j[idx] = rng.permutation(idx)
        hits = [np.abs(lines - g[f"{side}_actual"].iloc[jj] / g.unit.iloc[jj] * unit).min() <= TOLERANCE
                for side in ("HOD", "LOD") for lines, unit, jj in zip(g[f"{side}_lines"], g.unit, j)]
        out[name] = np.mean(hits)
    return pd.Series(out)


SAMPLES = {
    "same day of month": lambda d, past: past.index.map(lambda p: p.day == d.day).to_numpy(bool),
    "same weekday": lambda d, past: past.index.map(lambda p: p.weekday() == d.weekday()).to_numpy(bool),
    "all days": lambda d, past: np.full(len(past), True),
}


def known_bias(pick, bullish: pd.Series):
    return lambda d, past: pick(d, past) & (past.bullish == bullish[d]).to_numpy()


if __name__ == "__main__":
    stats = daily_stats(load_candles())
    methods = {f"{s}, {'raw' if c is None else c}": (SAMPLES[s], c)
               for s in SAMPLES for c in (None, "r5")}
    methods |= {f"{name}, bias known": (known_bias(pick, stats.bullish), c)
                for name, (pick, c) in list(methods.items()) if name.endswith(("raw", "r5"))}
    result = scorecard(stats, methods)
    result = result[result.day.isin(set.intersection(*(set(g.day) for _, g in result.groupby("method"))))]  # same days
    result.drop(columns=["HOD_lines", "LOD_lines", "HOD_levels", "LOD_levels"]).to_csv("scorecard.csv", index=False)
    print(f"{result.day.nunique()} days, {result.day.min()} .. {result.day.max()}; "
          f"hit = within {TOLERANCE:g} points of one of the top {TOP} bright lines\n")
    table = result.groupby("method").agg(
        n=("n", "median"), HOD_pinball=("HOD_pinball", "mean"), LOD_pinball=("LOD_pinball", "mean"),
        reached_75=("HOD_reached_75", "mean"), reached_50=("HOD_reached_50", "mean"), reached_25=("HOD_reached_25", "mean"),
        HOD_hit=("HOD_hit", "mean"), LOD_hit=("LOD_hit", "mean"))
    table["hit_random"] = random_hits(result)
    table["edge"] = (table.HOD_hit + table.LOD_hit) / 2 - table.hit_random  # > 0: bright lines beat chance
    print(table.sort_values("HOD_pinball").round(3).to_string())
    for d in map(date.fromisoformat, sys.argv[1:]):  # e.g. the days someone posted
        day = result[result.day == d]
        print(f"\n{d}: " + ("not scored (expiry week, contract roll or no 00:00 open)" if day.empty else
              f"HOD +{day.HOD_actual.iloc[0]:.2f}, LOD -{day.LOD_actual.iloc[0]:.2f} from the open"))
        for _, r in day.iterrows():
            print(f"  {r.method:36} HOD 75/50/25% {r.HOD_levels}, bright {r.HOD_lines} {'HIT' if r.HOD_hit else 'miss'}"
                  f" | LOD {r.LOD_levels}, bright {r.LOD_lines} {'HIT' if r.LOD_hit else 'miss'}")

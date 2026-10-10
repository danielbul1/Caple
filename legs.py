"""Legs: is the move that is running now over, and the next one starting?

A leg is a move of at least THETA = LEG x the day's expected range (levels.py's HAR yardstick, ~1/4
of a typical day) without giving back THETA against it (a zigzag). It turns the moment price is
THETA back from the leg's extreme, so the turn is only *known* THETA late; the question while a leg
runs is whether its extreme so far is already its end. After every 5m bar this is answered from:

- r: share of a leg already given back from the extreme. A driftless random walk, sitting between
  the extreme (r legs above) and the turn (1 - r below), reaches the turn first with odds exactly r
  (gambler's ruin): the baseline any statistics must beat (rw_end).
- g: how long the leg is so far, in legs; age: bars since the extreme; the hour of the day.

A logistic regression on those is refit every January on earlier years only (walk-forward, the
same as forecast_bias.py) and scored against the random walk; the trade enters against the leg
when the odds pass a cutoff, with its stop just past the extreme (if the leg goes on, the call was
wrong), and rides the new leg until the model calls its end too (then flips) or the zigzag turns.
The zigzag runs on without a break (THETA changes at midnight New York); only the days levels.py
keeps are scored and traded, and trades close by the end of the calendar day. (A zigzag restarted
each day leaves the day's last leg unfinished; dropping it told the model, through the hour, which
legs end before midnight: a look-ahead that inflated its edge.)

Run: python legs.py [DATE]           (the legs of DATE so far and the odds the running one is over)
     python legs.py backtest [LEG]   (walk-forward score and trades, LEG = leg size in day ranges)
"""

import sys
from datetime import date

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

import lse_source
from levels import use_yardstick
from quantistat import daily_stats, load_candles, today_market

LEG = 0.25        # leg size in expected day ranges
CUTOFF = 0.6      # odds the leg is over to trade it
TICK = 0.25
COST = 0.5        # points per round trip: a tick of slippage in and out, commission included
CUTOFFS = [0.5, 0.6, 0.7, 0.8]


def zigzag(high: np.ndarray, low: np.ndarray, theta) -> np.ndarray:
    """Per bar, known after its close: (direction +1/-1, 0 before the first leg; the leg's start;
    its extreme so far; the bar of that extreme). A bar that makes a new extreme extends the leg
    even if it also falls back a whole leg (5m bars rarely do both)."""
    out, theta = np.zeros((len(high), 4)), np.broadcast_to(theta, len(high))
    d, start, ext, ext_i, hi_i, lo_i = 0, np.nan, np.nan, -1, 0, 0
    for i in range(len(high)):
        if d == 0:
            hi_i, lo_i = (i if high[i] > high[hi_i] else hi_i), (i if low[i] < low[lo_i] else lo_i)
            if high[hi_i] - low[lo_i] >= theta[i]:  # the first leg runs from whichever came first
                d = 1 if lo_i < hi_i else -1
                start, ext, ext_i = (low[lo_i], high[hi_i], hi_i) if d == 1 else (high[hi_i], low[lo_i], lo_i)
        else:
            tip, back = (high[i], low[i]) if d == 1 else (low[i], high[i])
            if d * (tip - ext) > 0:
                ext, ext_i = tip, i
            elif d * (ext - back) >= theta[i]:
                d, start, ext, ext_i = -d, ext, back, i
        out[i] = d, start, ext, ext_i
    return out


def legs(day: pd.DataFrame, theta) -> pd.DataFrame:
    """5m bars plus dir, start, ext, age (bars since the extreme), r, g (see the module doc) and
    ended: 1 if the extreme known at that bar was the leg's end, NaN before the first leg and on
    the last leg, which has not turned yet."""
    z = zigzag(day.High.to_numpy(), day.Low.to_numpy(), theta)
    df = day.assign(dir=z[:, 0].astype(int), start=z[:, 1], ext=z[:, 2], age=np.arange(len(day)) - z[:, 3])
    leg = (df.dir != df.dir.shift()).cumsum()
    final = df.ext.groupby(leg).transform("last")
    df["ended"] = (df.ext == final).astype(float).where((df.dir != 0) & (leg != leg.iloc[-1]))
    df["r"] = df.dir * (df.ext - df.Close) / theta
    df["g"] = df.dir * (df.ext - df.start) / theta
    return df


def rw_end(r: np.ndarray) -> np.ndarray:
    """A driftless random walk's odds the leg is over: the share already given back (clipped for log loss)."""
    return np.clip(r, 0.01, 0.99)


def features(df: pd.DataFrame) -> np.ndarray:
    """Model inputs per bar: the random walk's odds as a logit, log leg size, log age, the hour."""
    p = rw_end(df.r.to_numpy())
    return np.column_stack([np.log(p / (1 - p)), np.log(df.g.clip(lower=1)), np.log1p(df.age),
                            np.eye(24)[df.index.hour]])


def trades(day: pd.DataFrame, p: np.ndarray, theta: float, cutoff: float = CUTOFF) -> list[dict]:
    """Trade one day's legs (output of legs()) on the odds p that each bar's leg is over."""
    out, side = [], 0
    cols = day[["dir", "ext", "Open", "High", "Low", "Close"]].itertuples(index=False)
    for i, (d, ext, o, high, low, close) in enumerate(cols):
        last = i == len(day) - 1
        if side and (low <= stop if side == 1 else high >= stop):
            exit_at = min(stop, o) if side == 1 else max(stop, o)  # a gap through the stop fills at the open
        elif side and (d == side and p[i] >= cutoff or last):
            exit_at = close
        else:
            exit_at = None
        if exit_at is not None:
            out.append({"time": entry_time, "side": side, "entry": entry, "exit": exit_at,
                        "points": side * (exit_at - entry) - COST})
            side = 0
        if side and d == side:
            stop = ext - side * theta  # our leg is confirmed: out where the zigzag would turn it
        if not side and d and p[i] >= cutoff and not last:
            side, entry, entry_time, stop = -d, close, day.index[i], ext + d * TICK
    return out


def load(leg: float = LEG) -> pd.DataFrame:
    """All 5m bars run through legs(), each day's theta from its yardstick (skipped days keep the
    last kept day's); only the kept days are returned."""
    stats = daily_stats(load_candles())
    use_yardstick(stats)
    kept = (stats.r5 * leg).dropna()
    bars = lse_source.fetch(timeframe="5m")
    bars = bars.assign(day=bars.index.date, theta=kept.reindex(sorted(set(bars.index.date))).ffill()
                       .reindex(bars.index.date).to_numpy()).dropna()
    df = legs(bars, bars.theta.to_numpy())
    return df[df.day.isin(kept.index)]


def fit(rows: pd.DataFrame) -> LogisticRegression:
    rows = rows[rows.ended.notna()]
    return LogisticRegression(max_iter=1000).fit(features(rows), rows.ended)


def walk_forward(df: pd.DataFrame) -> pd.Series:
    """Model odds for every bar in a leg, each year from a fit on the years before it only."""
    p = pd.Series(np.nan, index=df.index)
    years = df.index.year
    for y in sorted(set(years))[1:]:
        now = (years == y) & (df.dir != 0).to_numpy()
        p[now] = fit(df[years < y]).predict_proba(features(df[now]))[:, 1]
    return p


def log_loss(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def backtest(leg: float):
    df = load(leg)
    df["p"] = walk_forward(df)
    df = df[df.p.notna()]
    periods = {"2017-2021": df.index.year <= 2021, "2022-2026": df.index.year >= 2022}
    print(f"{df.day.nunique()} days, {df.day.min()} .. {df.day.max()}, leg = {leg} x expected range "
          f"(median {df.groupby('day').theta.first().median():.1f} points)\n")
    print("Is the running leg over? Log loss per bar (lower is better), averaged per day; t = paired over days")
    for name, keep in periods.items():
        s = df[keep & df.ended.notna().to_numpy()]
        base = s.ended.mean()
        ll = pd.DataFrame({"model": log_loss(s.p, s.ended), "rw": log_loss(rw_end(s.r), s.ended),
                           "base": log_loss(base, s.ended), "day": s.day}).groupby("day").mean()
        diff = ll.model - ll.rw
        print(f"  {name}: model {ll.model.mean():.4f}, random walk {ll.rw.mean():.4f}, base rate {ll.base.mean():.4f} "
              f"(model vs random walk {diff.mean() / ll.rw.mean():+.1%}, t {diff.mean() / diff.std() * np.sqrt(len(diff)):+.1f})")
        cal = s.groupby(pd.cut(s.p, np.linspace(0, 1, 11)), observed=True).agg(said=("p", "mean"), was=("ended", "mean"),
                                                                                 bars=("p", "size"))
        print("    calibration: " + ", ".join(f"{r.said:.2f}->{r.was:.2f}" for r in cal.itertuples()))
    print(f"\nTrades: against the leg when its odds pass the cutoff, {COST} points cost per round trip")
    print("signal  cutoff  period     trades  win%  avg pts  total pts  t")
    for signal, p in [("model", df.p.to_numpy()), ("rw", rw_end(df.r.to_numpy()))]:
        for c in CUTOFFS:
            t = pd.DataFrame([x for _, day in df.assign(q=p).groupby("day") for x in trades(day, day.q.to_numpy(), day.theta.iloc[0], c)])
            for name, keep in [("2017-2021", t.time.map(lambda ts: ts.year <= 2021)), ("2022-2026", t.time.map(lambda ts: ts.year >= 2022))]:
                x = t[keep].points
                print(f"{signal:6}  {c:6}  {name}  {len(x):6}  {(x > 0).mean():4.0%}  {x.mean():7.2f}  {x.sum():9.0f}  "
                      f"{x.mean() / x.std() * np.sqrt(len(x)):+.1f}")


def show(target: date):
    df = load()
    day = df[df.day == target]
    if day.empty:
        sys.exit(f"No 5m bars for {target} (or it is an expiry-week / contract-roll day levels.py skips).")
    model = fit(df[df.day < target])
    p = model.predict_proba(features(day))[:, 1] * (day.dir != 0).to_numpy()
    theta = day.theta.iloc[0]
    print(f"{target}: a leg = {theta:.1f} points ({LEG} x expected range); legs so far:")
    in_leg = day[day.dir != 0]
    for _, leg in in_leg.groupby((in_leg.dir != in_leg.dir.shift()).cumsum()):
        a, b = leg.iloc[0], leg.iloc[-1]
        end = "running" if b.name == day.index[-1] else f"{b.ext:.2f}"
        when = "before 00:00" if a.name == day.index[0] else f"{a.name:%H:%M}"
        print(f"  {'up  ' if a.dir == 1 else 'down'} {a.start:.2f} -> {end}  (confirmed {when})")
    now = day.iloc[-1]
    if now.dir == 0:
        print(f"No leg yet: the day's range is under {theta:.1f} points.")
        return
    print(f"Now {now.name:%H:%M}, close {now.Close:.2f}: {'up' if now.dir == 1 else 'down'} leg from {now.start:.2f}, "
          f"extreme {now.ext:.2f} ({now.age:.0f} bars ago), {now.r:.0%} of a leg given back, {now.g:.1f} legs long")
    print(f"  Odds it is over: model {p[-1]:.0%}, random walk {rw_end(np.array([now.r]))[0]:.0%}; "
          f"the turn is confirmed at {now.ext - now.dir * theta:.2f}")
    if p[-1] >= CUTOFF:
        print(f"  Signal: {'sell' if now.dir == 1 else 'buy'} {now.Close:.2f}, stop {now.ext + now.dir * TICK:.2f}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["backtest"]:
        backtest(float(args[1]) if len(args) > 1 else LEG)
    else:
        show(date.fromisoformat(args[0]) if args else today_market())

"""Search for a daily bias rule, tested the honest way (as nq-range-forecast does).

Every rule calls the calendar day (00:00-23:00 NY) bullish or bearish from what is
known at 00:00, or makes no call. Candidates come from ICT/PO3 lore and the
literature:
- prev_day: yesterday's direction (continuation; flips to reversal if that fits better)
- overnight: 00:00 open above the 18:00 Globex open (po3-research found no edge after midnight)
- close_location: yesterday closed in the upper half of its range
- discount: 00:00 open below yesterday's midpoint (ICT premium/discount)
- sweep: yesterday ran the day before's low and closed back above it (bullish), or ran
  its high and closed back below (bearish); otherwise no call (ICT/CRT liquidity sweep)
- trend: yesterday closed above its 20-day average close
- turn_of_month: last weekday of a month or the first three weekdays (calls bullish)
- seasonal_10y/5y/2y/agree: the market-bulls.com seasonal tendency the video reads
  (see seasonal.py); "agree" calls only when all three windows point the same way
- markov_*: 2nd-order Markov chain on direction, one rule per state of the last two days

Pre-registered gate: each rule's direction is fixed on 2016-2021 (flipped if it was
right less than half the time) and then scored once on 2022 onward. A rule passes
only if it beats always guessing the discovery period's majority side by more than
two standard errors on those out-of-sample days.

Result on ES.F 2016-05 .. 2026-10 (2,465 days, out-of-sample 2022+): no rule passed.
None beat "always bullish" (51.9% right out of sample); the best edges were within
noise and mostly negative. "Yesterday" means the previous kept day, so a day after a
dropped expiry week compares with the week before; that touches few days.

Run: LSE_API_KEY=... python bias.py   (forecast_bias.py tests Markov chains, SARIMAX and
ML models on 26 years of Yahoo daily sessions)
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd

import seasonal
from quantistat import daily_stats, load_candles

SPLIT = date(2022, 1, 1)


def turn_of_month(d: date) -> bool:
    next_weekday = d + timedelta(days=3 if d.weekday() == 4 else 1)
    weekdays_so_far = sum(date(d.year, d.month, k).weekday() < 5 for k in range(1, d.day + 1))
    return next_weekday.month != d.month or weekdays_so_far <= 3


def rules(stats: pd.DataFrame, globex: pd.Series) -> pd.DataFrame:
    """1.0 = bullish call, 0.0 = bearish call, NaN = no call."""
    p, p2 = stats.shift(1), stats.shift(2)
    mid = (p.high + p.low) / 2
    swept_low = (p.low < p2.low) & (p.close > p2.low)
    swept_high = (p.high > p2.high) & (p.close < p2.high)
    no_call = pd.Series(np.nan, index=stats.index)
    known = lambda cond, *src: cond.astype(float).where(pd.concat(src, axis=1).notna().all(axis=1))
    return pd.DataFrame({
        "prev_day": known(p.bullish == True, p.close),
        "overnight": known(stats.open > globex.reindex(stats.index), globex.reindex(stats.index)),
        "close_location": known(p.close > mid, p.close),
        "discount": known(stats.open < mid, p.close),
        "sweep": no_call.mask(swept_low & ~swept_high, 1.0).mask(swept_high & ~swept_low, 0.0),
        "trend": known(p.close > stats.close.rolling(20).mean().shift(), p.close),
        "turn_of_month": no_call.mask(pd.Series(stats.index.map(turn_of_month), index=stats.index), 1.0),
    })


def markov_rules(stats: pd.DataFrame) -> pd.DataFrame:
    """2nd-order Markov chain on day direction: one rule per state of the last two days,
    calling only in that state; evaluate() then fixes each state's next-day side."""
    name = lambda b: "bull" if b else "bear"
    p, p2 = stats.bullish.shift(1), stats.bullish.shift(2)
    return pd.DataFrame({f"markov_{name(a)}_{name(b)}": pd.Series(np.nan, index=stats.index).mask((p2 == a) & (p == b), 1.0)
                         for a in (False, True) for b in (False, True)})


def evaluate(rules: pd.DataFrame, bullish: pd.Series, split: date = SPLIT) -> pd.DataFrame:
    rows = []
    disc_days = bullish.index < split
    majority = bullish[disc_days].mean() >= 0.5  # the constant guess every rule must beat
    for name in rules:
        calls = rules[name].dropna() == 1
        disc = calls.index < split
        flipped = (calls[disc] == bullish[calls.index][disc]).mean() < 0.5
        hits = (calls ^ flipped) == bullish[calls.index]
        edge = hits[~disc].astype(float) - (bullish[calls.index][~disc] == majority)
        rows.append({"rule": name, "n_disc": disc.sum(), "disc_accuracy": hits[disc].mean(),
                     "flipped": flipped, "n_oos": (~disc).sum(), "oos_accuracy": hits[~disc].mean(),
                     "oos_baseline": (bullish[calls.index][~disc] == majority).mean(),
                     "edge": edge.mean(), "two_se": 2 * edge.sem(), "passed": edge.mean() > 2 * edge.sem()})
    return pd.DataFrame(rows)


def globex_opens(candles: pd.DataFrame) -> pd.Series:
    """The 18:00 reopen, keyed by the calendar day it leads into."""
    opens = candles.Open[candles.index.hour == 18]
    return pd.Series(opens.values, index=[t.date() + timedelta(days=1) for t in opens.index])


if __name__ == "__main__":
    candles = load_candles()
    stats = daily_stats(candles)
    globex = globex_opens(candles)
    globex = globex[~globex.index.duplicated()]
    calls = rules(stats, globex).join(markov_rules(stats)).join(seasonal.rules(seasonal.by_date(seasonal.daily_changes()), stats.index))
    table = evaluate(calls, stats.bullish)
    print(f"{len(stats)} days {stats.index[0]} .. {stats.index[-1]}, split {SPLIT}, "
          f"bullish {stats.bullish.mean():.1%}\n")
    print(table.round(3).to_string(index=False))

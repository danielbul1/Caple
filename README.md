# Caple

Small server that serves hourly ES candles from London Strategic Edge (LSE).

Pick a date in the calendar and get every 1h candle that closed before it (the
last one is the previous day 23:00 New York time) going back 729 days.

All data comes from LSE (https://londonstrategicedge.com/data): ES.F 1h bars since
mid 2016, cached to `lse_ES.F_1h.csv` (later runs only fetch new bars), and the US
economic calendar. The API key is in `LSE.md`; an `LSE_API_KEY` environment variable
overrides it. Any date with two years of LSE history before it (from mid 2018) can be picked.

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000.

## API

- `GET /api/available-dates`: dates that can be picked right now.
- `GET /api/candles?date=YYYY-MM-DD`: candles as JSON.
- `GET /api/candles?date=YYYY-MM-DD&format=csv`: candles as a CSV download.

## Today's HOD/LOD, no bias needed

```bash
python levels.py                   # today, after the latest candle
python levels.py 2026-10-09 9      # after the 9:00 candle ("open" = before the open)
python levels.py backtest          # walk-forward calibration on all the data
python levels.py 2025-01-02 open --2y   # learn only from the two years before the day, like the original tool
```

Besides the levels it prints the brightest heatmap levels as prices (where the most similar
past days ended) and saves `hodlod.png`, a QuantiStat-style "HOD/LOD Price Based" heatmap:
points from the 00:00 open (price on the right axis), HOD above 0, LOD below, one line per
2-point bin, brighter and thicker = more similar days ended there (bins under half the
brightest are hidden); dashed = the 75/50/25% levels, thin white = the open and the high/low
so far. The dashed levels are the calibrated forecast; a bright line alone is no better than a
random day's (see Scorecard).

At the open, or after any hourly candle, prints the chance the day's high and low
are already in and, if they go further, the prices reached on 75% / 50% / 25% of
similar past days (same hour, price in the same fifth of the range so far, scaled
to today's expected range). The expected range is a HAR blend (Corsi 2009) of yesterday's,
the 5-day and the 22-day Parkinson volatility from LSE's hourly bars, weights 0.59/0.29/0.10
on the log scale, fit on 2016-2021. It replaced the prior 5-day average range and recovers
what Yahoo's VIX9D gave (below). On LSE's 10 years walk-forward (2017-2026, 2,193 days)
everything is calibrated: at 9:00 the HOD was forecast already in on 39.0% of days and was
on 39.0%; the levels were reached on 76/53/28% of days. The miss of the median shrinks from
~17-20 points at the open to ~10-12 at 9:00 and ~5-6 at 12:00. From 2:00 on, the chance the HOD/LOD
is already in averages the similar days' share with a driftless random walk's (reflection
principle, with the share of the day's variance still to come after that hour): log loss 2-9%
lower at every checkpoint in both halves of the data.

## What improves accuracy (tested on LSE 2018-2026, walk-forward)

Change in HOD+LOD pinball loss vs the model above; negative is better, t in brackets.

| Idea (source) | open | 9:00 | 12:00 | Kept? |
|---|---|---|---|---|
| VIX9D instead of 5-day range (implied vol, Albers 2025) | -2% (-5) | -1% | ~0 | was; dropped with Yahoo |
| HAR on hourly Parkinson vol instead of 5-day range, 2022-2026 out of sample | -2.2% (-4.9) | -0.2% | -0.3% | yes (2:00/5:00 -1.2%, 15:00 -0.6%) |
| Update the yardstick each hour with today's Parkinson vol so far (rest-of-day range error -15% at 9:00, -10% at 12:00) | - | -0.2% (-0.8) | +0.6% (+1.3) | no: the size of the rest of the day is not how far past the high/low it goes |
| On FOMC/CPI days, a third of the weight on past days of the same event (2022-2026) | -0.1% (-2.1) | -0.1% | -0.3% (-2.0) | no: on the 143 event days -0.3% at 9:00, -1.8% (-1.5) at 12:00, noise |
| Overnight gap from yesterday's 16:00 close as a k-NN dimension (also at the open) | +0.1% | +0.4% (+1.9) | +0.6% (+2.9) | no, worse |
| Learn only from the last two years (`--2y`, as the original tool), 2022-2026 | +0.3% (+2.0) | +1.3% (+4.5) | +1.0% (+3.6) | no, worse at every hour (still calibrated); kept as an option |
| Average "already in" with a random walk's (reflection principle, the day's hourly variance profile; Mok, Lam & Li 2000) | - | log loss -2.9% / -1.8% (t -6.3 / -4.6) | -3.5% / -3.5% (t -6.3 / -6.1) | yes, from 2:00 on (2017-21 / 2022-26; 15:00 -8.6% / -3.4%, calls right +1-4 points); the random walk's levels alone were as good as the analogs but averaging them in did not help |
| Parkinson vol alone, 5-day mean or EWM (half-life 3) | -0.9/-1.1% (-3.7/-3.0) | ~0 | ~0 | no, HAR is better |
| HAR on daily ranges / + the 18:00-23:00 evening range | log-range error -6% / -5% (HAR-Parkinson -15%) | | | no |
| Position in fifths of the range so far, not halves | 0 | -3% (-5) | -4% (-6) | yes |
| HAR on daily ranges on top of VIX9D | -0.6% (-3) | ~0 | ~0 | no, too small |
| Match days on share of the range used so far ("% ATR used") | 0 | -0.3% | ~0 | no |
| Weight recent days more (half-life 150/500 days) | ~0 | ~0 | ~0 | no |
| LightGBM quantile regression (7-9 features) | +0.6% worse | -2% (-4) | -4% (-6) | no: fifths do the same simply |
| Day-of-month / weekday samples (QuantiStat) | worse/0 | - | - | no |
| Bright heatmap lines | no better than a random day | | | no |

The size of the day is predictable (implied volatility does most of it); its direction is
not, so no level set beats ~22/27 points of pinball at the open. During the day, where price
sits in its range so far is the useful information.

## Scorecard: which levels are right, every day

```bash
python scorecard.py 2024-12-26 2025-01-02   # all methods, 2018-2026, plus those days' calls
```

Every day since 2018, before the open, each method builds HOD/LOD levels from earlier days
only and is scored against the day (per-day rows in `scorecard.csv`). On 2,089 days (VIX9D
numbers are from before Yahoo was dropped; scorecard.py now compares raw points and r5):

- Scaling matters most: raw points (QuantiStat) lose 28.3/31.5 points (HOD/LOD pinball)
  and their "75%" level is reached on 86% of days (prices rose since 2018); scaled by VIX9D
  22.9/27.4 and calibrated (76/51/27%).
- Which past days you pick barely matters: same day of month (QuantiStat), same weekday
  and all days are within noise of each other once scaled by VIX9D.
- The bright heatmap lines know nothing about the day: the HOD/LOD lands within 3 points of
  one of the 3 brightest lines on ~31% of days, and so does another random day's HOD/LOD
  (with the bias known too, against another day of the same bias).
- Only knowing the day's bias (its real close vs open) helps the levels: pinball 18/22. No
  rule found that bias in advance (bias.py), so this is the ceiling of a perfect hand-picked
  bias, not something achievable.

## Daily journal: was I right today?

```bash
python journal.py              # yesterday (run just after midnight New York)
python journal.py 2026-10-09   # any finished days
python journal.py 2024-10-10..2026-10-09   # every day in a range
```

Replays levels.py's forecast for a finished day (before the open and after the
2/5/9/12/15:00 candles, from earlier days only), marks each call right or WRONG and whether
the HOD/LOD landed between the 75% and 25% levels (`*_in_band`), appends it to the tracked
`journal.csv` and prints the running record. A scheduled routine runs it every trading day
and pushes the journal.

Backfilled on 2026-10-10 with every scored day of the two years before (2024-10-10 .. 2026-10-09,
475 days; expiry weeks, contract rolls and holidays are skipped):

| hour | HOD call right | LOD call right | HOD in band | LOD in band | HOD off | LOD off |
|---|---|---|---|---|---|---|
| open | 100% | 100% | 52% | 50% | 24.6 | 28.2 |
| 2:00 | 87% | 83% | 53% | 50% | 23.0 | 26.8 |
| 5:00 | 80% | 75% | 50% | 51% | 20.2 | 23.6 |
| 9:00 | 74% | 72% | 53% | 55% | 13.7 | 16.1 |
| 12:00 | 81% | 74% | 55% | 51% | 6.9 | 7.8 |
| 15:00 | 82% | 86% | 51% | 44% | 2.7 | 2.8 |

"In band" should be ~50% if the levels are honest, and it is. "Off" is points between the
best-guess line and the real HOD/LOD. At the open, "call right" only says the high/low was
still to come, which is almost always true, so it carries no information there.

## Why the percentages look low, and what is the best possible

- "In band" ~50% is the target, not a failure: the 75%-25% band is built to catch half the
  days. Any band can score higher by being wider, which says nothing. What makes a forecast
  better is a narrower band at the same honest rate (lower pinball / points off).
- "Call right" (is the HOD/LOD already in?) is close to its ceiling. If ES were a pure random
  walk with exactly known volatility, the best possible call (reflection principle, with ES's
  hour-by-hour share of the day's variance) would be right on 78/73% (HOD/LOD) of days at 9:00
  and 77/73% at 12:00 (2018-2026). Walk-forward we get 72-74/69-71% at 9:00 and 77-79/75-77% at
  12:00. Most of what is left is the rest of the day's random path, which no model sees; the
  small edge over a random walk at 12:00 is what real intraday behaviour adds.
- What others do, tested walk-forward (models picked on 2018-2021 in a separate bake-off): the
  analog family wins. k-NN analogs (the Analog Ensemble of weather forecasting) on points below
  the high / above the low so far, blended half and half with the fifth-of-range days, is what
  levels.py now uses. Against the fifths alone (`python levels.py backtest`, 2,210 days):

  | | 2:00 | 5:00 | 9:00 | 12:00 | 15:00 |
  |---|---|---|---|---|---|
  | "already in" log loss (HOD/LOD), 2017-2021 | -2.6/-1.4% | -0.7/-0.9% | -0.9/-1.1% | -1.1/-0.8% | -0.8/-1.3% |
  | "already in" log loss (HOD/LOD), 2022-2026 | -1.5/-1.1% | -1.8/-2.2% | -1.5/-2.2% | -3.8/-4.4% | -3.6/-3.5% |
  | calls right (HOD/LOD), 2017-2021 | 88/82% = | 79/69% (+1/+2) | 74/71% (+1/+1) | 77/77% (0/+1) | 78/85% (-2/-2) |
  | calls right (HOD/LOD), 2022-2026 | 88/86% = | 79/76% (+1/+1) | 72/69% (0/+2) | 79/75% (+1/0) | 82/85% (+3/0) |
  | pinball (HOD/LOD), 2022-2026 | +0.1/-0.1% | -0.4/-0.4% | -0.6/-0.5% | -0.6/-0.8% | -1.6/-1.5% |

  On 2017-2021 the pinball barely moved (-0.5% to +0.6%). LightGBM quantile models (hour, distances
  to the high/low, range so far, prior range, realized/implied vol, weekday, FOMC/CPI) were no
  better alone and, added to the blend, only helped at 15:00, so they were left out; adding
  range so far or realized/implied vol to the k-NN, or k=300, made it worse.

## Live HOD/LOD price heatmap

The top of the page (`GET /api/lines?date=YYYY-MM-DD`, default the latest day) draws the
QuantiStat "Price Based" heatmap for today: points from the 00:00 open, HOD above 0, LOD
below, one horizontal line per 2-point bin where similar past days that went past the
high/low so far ended (scaled to today's yardstick; bins of a single day are hidden),
brighter and thicker = more days. The dashed white lines are the high/low so far with the
chance it is already the final one. It is recomputed before the open and after every
hourly candle (the forming candle counts, data refreshes every 2 minutes, the page every
minute); the "מצב" picker replays any earlier hour of the day.
The page runs on LSE's history since 2016, so any date since then can be viewed, and the
forecast uses the same history it was tested on. It only shows bars LSE has closed, so the
hour still forming appears once LSE publishes it.
No single level is "touch once and it's the HOD": walk-forward (`python levels.py backtest`,
`*_past_line`) on days price reached the median level, it went on another ~25-38 points on
average before 9:00 and ~17-24 after 12:00.

## Legs: is the running move over?

```bash
python legs.py                  # today's legs so far and the odds the running one is over
python legs.py 2026-10-09
python legs.py backtest [LEG]   # walk-forward, LEG = leg size in expected day ranges (default 0.25)
```

The HOD/LOD question asked about any move instead of the day: on LSE's 5m bars (since 2016,
`lse_ES.F_5m.csv`) a leg is a move of at least a quarter of the day's expected range (levels.py's
HAR yardstick, median 11.5 points) without a pullback that big (a zigzag). The turn is only
confirmed a whole leg late, so after every 5m bar the question is whether the extreme so far is
already the end. A driftless random walk answers it with the share of a leg already given back
(gambler's ruin); a logistic regression adds the leg's length so far, bars since the extreme and
the hour, refit every January on earlier years. Trading it: sell an up leg (buy a down leg) when
the odds pass a cutoff, stop a tick past the extreme, ride the new leg until its own end is called
(flip) or the zigzag turns it, flat by midnight, 0.5 points cost per round trip.

Walk-forward, 2,326 days (2017-2026):

| leg size | "over?" log loss, model vs random walk, 2017-21 / 2022-26 | trades at cutoff 0.8, pts/trade 2017-21 / 2022-26 |
|---|---|---|
| 0.15 x range (6.9 pts) | -0.5% (t -4.5) / -0.0% (t -0.5) | -0.67 (t -9.3) / -0.52 (t -4.4) |
| 0.25 x range (11.5 pts) | +0.2% (t +2.2) / +0.1% (t +1.7) | -0.56 (t -3.9) / -0.34 (t -1.4) |
| 0.5 x range (23.1 pts) | +0.7% (t +2.5) / +0.2% (t +1.7) | -1.07 (t -3.2) / +0.56 (t +1.0) |

The odds are calibrated (said 0.65 -> was 0.66) but they are the random walk's: once the
pullback is known, the leg's length, its age and the hour add nothing, and every cutoff loses
about the cost per trade (gross ~0) for the model and the plain pullback rule alike (the one
positive cell, 23-point legs on 2022-26, lost on 2017-21 and the pullback rule matches it). So the turn
of a leg can't be told at the moment it happens from price alone, the same as the day's
direction (bias.py, forecast_bias.py). A first version restarted the zigzag every midnight and
dropped the day's unfinished last leg; that told the model, through the hour, which legs end
before midnight, and showed a false -4% edge (t -11).

## QuantiStat charts

The charts and backtest use LSE's 10 years of ES.F 1h bars.

```bash
python quantistat.py 2026-10-12 7840   # target day (default today), optional 00:00 open
```

Keeps only past days on the target's
weekday (calendar days 00:00-23:00 NY time). Quarterly expiry weeks and days where
the continuous series jumps between contracts are dropped (bad HOD/LOD). Saves `time_based.png` (hour
of HOD/LOD split by bullish/bearish day) and `price_based.png` (HOD/LOD distance
from the open in points, split by bias; above 0 = HOD, below 0 = LOD, brighter =
more often), and prints per bias the usual HOD/LOD hours and the levels the
HOD/LOD reached on 75% / 50% / 25% of days (as prices when the open is given).
Levels are rescaled to today's volatility (each day's distance divided by its
prior 5-day average range, times today's), so old low-volatility years still count.
`python backtest.py` checks, walk-forward, whether picking days by day-of-month
beats same weekday or simply all days (bias taken as known).
`python bias.py` tests 7 simple daily bias rules (previous day, overnight vs
18:00 open, close location, premium/discount, liquidity sweep, trend, turn of
month): direction fixed on 2016-2021, scored once on 2022+. None beat always
guessing bullish, so the charts still take the bias as your input.
`python seasonal.py 2026-10-12` draws the market-bulls.com style seasonal
tendencies (10/5/2-year average path of LSE's daily closes, since mid 2016) and prints
that day's seasonal bias; bias.py tests it too, and it does not beat always
bullish either (2022+: 50.9% when all three windows agree vs 49.7%).
`python forecast_bias.py` tests the Discord "statistical data" ideas (markov-process,
sarimax, bias-forecasting) walk-forward on LSE's calendar days (2,445 days since mid 2016,
the days quantistat.py keeps): each model is refit every January on earlier years only and
scored on 2019-2026 (1,851 days) by Brier score against the base rate. None passes (mean
edge > 2 SE); every one is worse than the base rate, gradient boosting significantly:

| model | Brier edge (x1e-4) | 2 SE | accuracy | always bullish |
|---|---|---|---|---|
| Markov chain, last 1/2/3 days | -4.6 / -6.6 / -14.4 | 10.7 / 13.1 / 19.6 | 53.3-54.3% | 54.3% |
| Markov, last 2 days + big/small range | -25.5 | 21.7 | 53.1% | 54.3% |
| SARIMAX(1,0,1)x(1,0,1,5) + range ratio | -19.4 | 30.5 | 52.5% | 54.3% |
| logistic regression, 8 features | -14.8 | 23.4 | 53.3% | 54.3% |
| gradient-boosted trees, same features | -48.7 (worse) | 32.6 | 52.9% | 54.3% |

The Markov chains mostly reduce to "always bullish" (bullish was the likelier side after
almost every state). The same models on 26 years of Yahoo daily sessions (2000-2026, before
Yahoo was dropped) gave the same answer. Daily direction stays unpredictable, so the bias
stays your input.
Tests: `pip install pytest && pytest`.

# Caple

Small server that serves hourly ES=F candles from Yahoo Finance.

Pick a date in the calendar and get every 1h candle that closed before it (the
last one is the previous day 23:00 New York time) going back 729 days.

Yahoo only serves 1h data from the last 730 days, counted from the current
moment, so only dates whose full history fits in that window can be picked.
In practice that's today, and early in the morning also yesterday.

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
python levels.py 2026-10-09 9      # after the 9:00 candle ("open" = before the open)
python levels.py backtest          # walk-forward calibration on all the data
```

At the open, or after any hourly candle, prints the chance the day's high and low
are already in and, if they go further, the prices reached on 75% / 50% / 25% of
similar past days (same hour, price in the same fifth of the range so far, scaled
to today's VIX9D implied daily move). On LSE's 10 years walk-forward (2017-2026, 2,210
days) VIX9D beat the prior 5-day range at the open (pinball -2%, paired t -5), less so
later; VIX1D was no better and only starts in 2023. `python levels.py backtest r5` scores
the old yardstick. Everything is calibrated: at 9:00 the HOD was forecast already in on
39.5% of days and was on 39.0%; the levels were reached on 76/54/27% of days. The miss of
the median shrinks from ~17-20 points at the open to ~10-12 at 9:00 and ~6 at 12:00.

## What improves accuracy (tested on LSE 2018-2026, walk-forward)

Change in HOD+LOD pinball loss vs the model above; negative is better, t in brackets.

| Idea (source) | open | 9:00 | 12:00 | Kept? |
|---|---|---|---|---|
| VIX9D instead of 5-day range (implied vol, Albers 2025) | -2% (-5) | -1% | ~0 | yes |
| Position in fifths of the range so far, not halves | 0 | -3% (-5) | -4% (-6) | yes |
| HAR range forecast (Corsi 2009) on top of VIX9D | -0.6% (-3) | ~0 | ~0 | no, too small |
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
only and is scored against the day (per-day rows in `scorecard.csv`). On 2,089 days:

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
No single level is "touch once and it's the HOD": walk-forward (`python levels.py backtest`,
`*_past_line`) on days price reached the median level, it went on another ~25-38 points on
average before 9:00 and ~17-24 after 12:00.

## QuantiStat charts

With a free London Strategic Edge key in `LSE_API_KEY`
(https://londonstrategicedge.com/data) the charts and backtest use 10 years of
ES.F 1h bars (cached to `lse_ES.F_1h.csv`, only new bars are fetched later);
without it they use Yahoo's last 2 years. On the 456 days both cover they agree
on the HOD hour 98% of the time.

```bash
python quantistat.py 2026-10-12 7840   # target day (default today), optional 00:00 open
```

Uses the same two years of 1h candles and keeps only past days on the target's
weekday (calendar days 00:00-23:00 NY time). Quarterly expiry weeks and days where
Yahoo's continuous ES=F jumps between contracts are dropped (bad HOD/LOD). Saves `time_based.png` (hour
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
tendencies (10/5/2-year average path from Yahoo daily ES since 2000) and prints
that day's seasonal bias; bias.py tests it too, and it does not beat always
bullish either (2022+: 50.9% when all three windows agree vs 49.7%).
Tests: `pip install pytest && pytest`.

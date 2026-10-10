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
similar past days (same hour, price in the same half of the range so far, scaled
to today's VIX9D implied daily move). On LSE's 10 years walk-forward (2017-2026, 2,210
days) VIX9D beat the prior 5-day range at the open (pinball -2%, paired t -5), less so
later; VIX1D was no better and only starts in 2023. `python levels.py backtest r5` scores
the old yardstick. Everything is calibrated: at 9:00 the HOD was forecast already in on
39.5% of days and was on 39.0%; the levels were reached on 76/54/27% of days. The miss of
the median shrinks from ~17-20 points at the open to ~10-12 at 9:00 and ~6 at 12:00.

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

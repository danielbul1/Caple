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

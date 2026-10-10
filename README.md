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

```bash
python quantistat.py 2026-10-12   # target day; default is today
```

Uses the same two years of 1h candles and keeps only past days with the target's
day-of-month (calendar days 00:00-23:00 NY time). Quarterly expiry weeks and days where
Yahoo's continuous ES=F jumps between contracts are dropped (bad HOD/LOD). Saves `time_based.png` (hour
of HOD/LOD split by bullish/bearish day) and `price_based.png` (HOD/LOD distance
from the open in points; above 0 = HOD, below 0 = LOD, brighter = more often).
Tests: `pip install pytest && pytest`.

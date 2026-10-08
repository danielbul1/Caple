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

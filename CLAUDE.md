# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A small Flask server that serves hourly ES=F (S&P 500 e-mini futures) candles from Yahoo Finance via `yfinance`. The user picks a date D and gets every 1h candle that closed before D (the last is D-1 23:00 New York time), going back `LOOKBACK_DAYS` (729) days. Data comes back as JSON or as a CSV download.

## Commands

```bash
pip install -r requirements.txt
python app.py          # serves on http://localhost:5000
```

There are no tests, linter or build step. The frontend is a single static file with no build. Fetching data needs network access to Yahoo Finance.

## Architecture

- `app.py` holds all backend logic: date-window math, availability checks, the Yahoo fetch, an in-memory cache, and three routes (`/`, `/api/available-dates`, `/api/candles`).
- `static/index.html` is the whole UI: vanilla JS that calls `/api/available-dates` to fill a date picker, then `/api/candles?date=...`, and links to the `&format=csv` variant. **UI text is in Hebrew (RTL).**

### The 730-day constraint (key domain rule)

Yahoo only serves 1h data whose start lies within the last 730 days, counted from the current moment, not from a date. `is_available()` allows a date only when its whole lookback window fits inside that moving boundary, with a `SAFETY_MARGIN` buffer. So in practice only today (and, early in the day, yesterday) can be picked. `/api/available-dates` scans just the last 7 days for that reason. Changing `LOOKBACK_DAYS`, `YAHOO_WINDOW_DAYS` or `INTERVAL` changes which dates are selectable.

### Timezones

The "current day" and all output timestamps use `America/New_York` (`MARKET_TZ`). The Yahoo boundary is computed in UTC. `window_for()` returns an exclusive end date, which is why data stops at D-1 23:00.

### Caching and errors

`_cache` is a process-local dict keyed by picked date. It is never evicted and is lost on restart. Status codes on `/api/candles`: 400 for a bad or missing date, 422 for a date outside Yahoo's window, 502 for a Yahoo or network failure.

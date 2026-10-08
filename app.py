"""Small server that serves two years of hourly ES=F candles from Yahoo Finance.

The user picks a date D. The response holds every 1h candle that closed before
D (the last one is D-1 23:00 New York time) going back LOOKBACK_DAYS days.

Yahoo only serves 1h data whose start lies within the last 730 days, counted
from the current moment. A date is selectable only when its full lookback fits
inside that window, so in practice only today (and early in the morning,
yesterday) can be picked.
"""

from datetime import date, datetime, time, timedelta, timezone
from io import StringIO
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf
from flask import Flask, Response, jsonify, request, send_from_directory

SYMBOL = "ES=F"
INTERVAL = "1h"
LOOKBACK_DAYS = 729
YAHOO_WINDOW_DAYS = 730
# Keep a small buffer from Yahoo's moving boundary so a request built just
# before the boundary passes doesn't fail by the time it reaches Yahoo.
SAFETY_MARGIN = timedelta(minutes=10)
MARKET_TZ = ZoneInfo("America/New_York")

app = Flask(__name__, static_folder="static")
_cache: dict[date, pd.DataFrame] = {}


def today_market() -> date:
    return datetime.now(MARKET_TZ).date()


def window_for(picked: date) -> tuple[date, date]:
    """Return (start, end) dates; end is exclusive, so data stops at picked-1 23:00."""
    return picked - timedelta(days=LOOKBACK_DAYS), picked


def is_available(picked: date) -> bool:
    if picked > today_market():
        return False
    start, _ = window_for(picked)
    start_moment = datetime.combine(start, time.min, MARKET_TZ)
    oldest_allowed = datetime.now(timezone.utc) - timedelta(days=YAHOO_WINDOW_DAYS)
    return start_moment >= oldest_allowed + SAFETY_MARGIN


def fetch_candles(picked: date) -> pd.DataFrame:
    if picked in _cache:
        return _cache[picked]
    start, end = window_for(picked)
    df = yf.download(
        SYMBOL,
        start=start.isoformat(),
        end=end.isoformat(),
        interval=INTERVAL,
        progress=False,
        auto_adjust=False,
        multi_level_index=False,
    )
    if df.empty:
        raise RuntimeError("Yahoo returned no data for this range")
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.index = df.index.tz_convert(MARKET_TZ)
    df.index.name = "Datetime"
    _cache[picked] = df
    return df


def parse_date(raw: str | None) -> date | None:
    try:
        return date.fromisoformat(raw or "")
    except ValueError:
        return None


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/available-dates")
def available_dates():
    today = today_market()
    # Only the last few days can ever qualify; checking a week is plenty.
    days = [today - timedelta(days=i) for i in range(7)]
    return jsonify(
        {
            "today": today.isoformat(),
            "available": sorted(d.isoformat() for d in days if is_available(d)),
            "lookback_days": LOOKBACK_DAYS,
            "symbol": SYMBOL,
        }
    )


@app.get("/api/candles")
def candles():
    picked = parse_date(request.args.get("date"))
    if picked is None:
        return jsonify({"error": "Pass date=YYYY-MM-DD"}), 400
    if not is_available(picked):
        return jsonify({"error": f"{picked} has no full {LOOKBACK_DAYS}-day history on Yahoo"}), 422
    try:
        df = fetch_candles(picked)
    except Exception as exc:  # network errors, Yahoo refusals
        return jsonify({"error": str(exc)}), 502

    if request.args.get("format") == "csv":
        buf = StringIO()
        df.to_csv(buf)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=ES_1h_until_{picked}.csv"},
        )

    start, _ = window_for(picked)
    rows = [
        {
            "time": ts.strftime("%Y-%m-%d %H:%M"),
            "open": float(r.Open),
            "high": float(r.High),
            "low": float(r.Low),
            "close": float(r.Close),
            "volume": int(r.Volume),
        }
        for ts, r in df.iterrows()
    ]
    return jsonify(
        {
            "symbol": SYMBOL,
            "date": picked.isoformat(),
            "requested_start": start.isoformat(),
            "first": rows[0]["time"],
            "last": rows[-1]["time"],
            "count": len(rows),
            "candles": rows,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

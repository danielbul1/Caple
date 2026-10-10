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
from math import isnan
from time import monotonic
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
LIVE_TTL = 120
_live: tuple[float, pd.DataFrame] | None = None


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
    _cache[picked] = download(*window_for(picked))
    return _cache[picked]


def live_candles() -> tuple[pd.DataFrame, pd.Series]:
    """The last ~2 years of 1h candles up to now (the current hour still forming) and VIX1D's
    daily closes, refreshed at most every LIVE_TTL seconds."""
    from levels import vix1d_closes  # levels imports this module

    global _live
    if _live is None or monotonic() - _live[0] > LIVE_TTL:
        today = today_market()
        candles = download(today - timedelta(days=LOOKBACK_DAYS - 1), today + timedelta(days=1))
        _live = (monotonic(), candles, vix1d_closes())
    return _live[1], _live[2]


def download(start: date, end: date) -> pd.DataFrame:
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


@app.get("/api/lines")
def lines():
    """The HOD/LOD line of a day (default: the latest), as forecast before the open and after
    each hourly candle so far; the page redraws it live."""
    from levels import day_lines, today_scale, use_vix1d  # levels imports this module
    from quantistat import daily_stats

    try:
        candles, closes = live_candles()
    except Exception as exc:  # network errors, Yahoo refusals
        return jsonify({"error": str(exc)}), 502
    target = parse_date(request.args.get("date")) or candles.index[-1].date()
    day = candles[candles.index.date == target]
    if len(day) == 0 or day.index[0].hour != 0:
        return jsonify({"error": f"No 00:00 candle for {target}"}), 404
    stats = daily_stats(candles)
    yardstick, closes = use_vix1d(stats, closes=closes)
    rows = day_lines(candles, stats, target, today_scale(stats, yardstick, closes, target, day.Open.iloc[0]))
    num = lambda x: None if isnan(x) else round(float(x), 2)
    return jsonify(
        {
            "date": target.isoformat(),
            "live": target == today_market(),
            "yardstick": yardstick,
            "candles": [
                {"hour": ts.hour, "open": float(r.Open), "high": float(r.High), "low": float(r.Low), "close": float(r.Close)}
                for ts, r in day.iterrows()
            ],
            "lines": [
                {"hour": None if r["hour"] is None else int(r["hour"]), "n": r["n"],
                 "high": float(r["high"]), "low": float(r["low"]),
                 **{f"{side.lower()}_done": num(r[side]["done"]) for side in ("HOD", "LOD")},
                 **{f"{side.lower()}_heat": r[side]["heat"] for side in ("HOD", "LOD")}}
                for r in rows
            ],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

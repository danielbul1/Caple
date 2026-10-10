"""Small server that serves hourly ES candles from London Strategic Edge (LSE).

The user picks a date D. The response holds every 1h candle that closed before
D (the last one is D-1 23:00 New York time) going back LOOKBACK_DAYS days. LSE's
history starts mid 2016, so any date with that much history before it can be picked.
"""

from datetime import date, datetime, timedelta
from io import StringIO
from math import isnan
from time import monotonic
from zoneinfo import ZoneInfo

import pandas as pd
from flask import Flask, Response, jsonify, request, send_from_directory

SYMBOL = "ES.F"
LOOKBACK_DAYS = 729
MARKET_TZ = ZoneInfo("America/New_York")

app = Flask(__name__, static_folder="static")
LIVE_TTL = 120
_live: tuple[float, pd.DataFrame] | None = None


def today_market() -> date:
    return datetime.now(MARKET_TZ).date()


def window_for(picked: date) -> tuple[date, date]:
    """Return (start, end) dates; end is exclusive, so data stops at picked-1 23:00."""
    return picked - timedelta(days=LOOKBACK_DAYS), picked


def live_candles() -> pd.DataFrame:
    """LSE's 1h candles since 2016 up to its latest bar, refreshed at most every LIVE_TTL seconds."""
    import lse_source  # lse_source imports this module

    global _live
    if _live is None or monotonic() - _live[0] > LIVE_TTL:
        _live = (monotonic(), lse_source.fetch())
    return _live[1]


def available(candles: pd.DataFrame) -> list[date]:
    first = candles.index[0].date() + timedelta(days=LOOKBACK_DAYS)
    return [first + timedelta(days=i) for i in range((today_market() - first).days + 1)]


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
    try:
        days = available(live_candles())
    except Exception as exc:  # network errors, LSE refusals
        return jsonify({"error": str(exc)}), 502
    return jsonify(
        {
            "today": today_market().isoformat(),
            "available": [d.isoformat() for d in days],
            "lookback_days": LOOKBACK_DAYS,
            "symbol": SYMBOL,
        }
    )


@app.get("/api/candles")
def candles():
    picked = parse_date(request.args.get("date"))
    if picked is None:
        return jsonify({"error": "Pass date=YYYY-MM-DD"}), 400
    try:
        all_candles = live_candles()
    except Exception as exc:  # network errors, LSE refusals
        return jsonify({"error": str(exc)}), 502
    if picked not in available(all_candles):
        return jsonify({"error": f"{picked} has no full {LOOKBACK_DAYS}-day history on LSE"}), 422
    start, end = window_for(picked)
    df = all_candles[(all_candles.index.date >= start) & (all_candles.index.date < end)]

    if request.args.get("format") == "csv":
        buf = StringIO()
        df.to_csv(buf)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=ES_1h_until_{picked}.csv"},
        )

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
    from levels import day_lines  # levels imports this module
    from quantistat import daily_stats, recent_range

    try:
        candles = live_candles()
    except Exception as exc:  # network errors, LSE refusals
        return jsonify({"error": str(exc)}), 502
    target = parse_date(request.args.get("date")) or candles.index[-1].date()
    day = candles[candles.index.date == target]
    if len(day) == 0 or day.index[0].hour != 0:
        return jsonify({"error": f"No 00:00 candle for {target}"}), 404
    stats = daily_stats(candles)
    rows = day_lines(candles, stats, target, recent_range(stats, target))
    num = lambda x: None if isnan(x) else round(float(x), 2)
    return jsonify(
        {
            "date": target.isoformat(),
            "live": target == today_market(),
            "yardstick": "r5",
            "candles": [
                {"hour": ts.hour, "open": float(r.Open), "high": float(r.High), "low": float(r.Low), "close": float(r.Close)}
                for ts, r in day.iterrows()
            ],
            "lines": [
                {"hour": None if r["hour"] is None else int(r["hour"]), "n": r["n"],
                 "high": float(r["high"]), "low": float(r["low"]),
                 **{f"{side.lower()}_done": num(r[side]["done"]) for side in ("HOD", "LOD")},
                 **{f"{side.lower()}_heat": r[side]["heat"] for side in ("HOD", "LOD")},
                 **{f"{side.lower()}_levels": [num(x) for x in r[side]["levels"]] for side in ("HOD", "LOD")}}
                for r in rows
            ],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

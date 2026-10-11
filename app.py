"""Caple: a small server for the HOD/LOD page and hourly ES candles from London Strategic Edge (LSE).

/api/price-based draws the page's Price Based heatmap (see its docstring). /api/candles: the user
picks a date D and gets every 1h candle that closed before D (the last one is D-1 23:00 New York
time) going back LOOKBACK_DAYS days. LSE's history starts mid 2016, so any date with that much
history before it can be picked.
"""

from datetime import date, datetime, timedelta
from io import StringIO
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


@app.get("/api/price-based")
def price_based():
    """Price Based heatmap of the first day after the End Date (default: the latest day): where
    the HOD (above 0) and LOD (below 0) of similar earlier days ended, in 1-point cells counted
    from the 00:00 open, cells with a single day left out. at=open is before the open, at=H after
    the H:00 candle, no at after the latest candle (live for today). Only candles up to that point
    are used, so nothing later can change the answer."""
    from levels import MIN_DAYS, day_lines, today_yardstick, use_yardstick  # levels imports this module
    from quantistat import daily_stats

    raw_end, at = request.args.get("end"), request.args.get("at")
    end = parse_date(raw_end)
    if (raw_end and end is None) or at not in (None, "open", *map(str, range(24))):
        return jsonify({"error": "Enter the End Date as YYYY-MM-DD and the time as open or an hour from 0 to 23."}), 400
    try:
        candles = live_candles()
    except Exception as exc:  # network errors, LSE refusals
        return jsonify({"error": str(exc)}), 502
    days = candles.index.date
    opens = days[candles.index.hour == 0]
    later = opens if end is None else opens[opens > end]
    if len(later) == 0:
        return jsonify({"error": f"No trading day after {end} yet. Pick an earlier End Date."}), 404
    target = later.max() if end is None else later.min()
    hours = sorted(set(candles.index.hour[days == target]))
    hour = None if at == "open" else hours[-1] if at is None else int(at)
    if hour is not None and hour not in hours:
        return jsonify({"error": f"{target} has no {hour}:00 candle. Pick an hour that has one, or before the open."}), 404
    known = candles[(days < target) | ((days == target) & (candles.index.hour <= (hour or 0)))]
    stats = daily_stats(known)
    use_yardstick(stats)
    rows = day_lines(known, stats, target, today_yardstick(stats, target))
    row, open_ = rows[0] if hour is None else rows[-1], float(known.Open[known.index.date == target].iloc[0])
    return jsonify(
        {
            "symbol": SYMBOL,
            "date": target.isoformat(),
            "end": max(d for d in days if d < target).isoformat(),
            "live": target == today_market(),
            "hours": [int(h) for h in hours],
            "hour": hour,
            "open": open_,
            "high": float(row["high"]),
            "low": float(row["low"]),
            "n": row["n"],
            "cells": [{"side": side, "points": round(p - open_), "days": c}
                      for side in ("HOD", "LOD") for p, c in row[side]["heat"] if c >= MIN_DAYS],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

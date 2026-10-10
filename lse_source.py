"""Ten years of hourly ES candles from London Strategic Edge (LSE), the only data source.

The LSE vault has ES.F 1h back to mid 2016. The key is the LSE_API_KEY environment variable,
else the one in LSE.md. The full pull is ~13 requests of 5000 rows, cached to
lse_ES.F_1h.csv; later runs only fetch new bars.
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

from app import MARKET_TZ

VAULT = "https://api.londonstrategicedge.com/vault"
# Days these releases land on behave differently (FOMC: ranges ~1.3x normal, the high or low
# often comes after the 14:00 decision; CPI ~1.2x), so levels.py matches them separately.
EVENTS = {"Fed Interest Rate Decision": "FOMC", "Core Inflation Rate MoM": "CPI"}
PAGE = 5000  # the API's row cap per request
HEADERS_UA = "caple (+https://github.com/danielbul1/caple)"  # the API refuses Python's default User-Agent


def to_frame(rows: list[dict]) -> pd.DataFrame:
    """API rows (bar-open time in UTC) -> the same New York candles app.py serves."""
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.ts).dt.tz_localize("UTC").dt.tz_convert(MARKET_TZ).rename("Datetime")
    return df.rename(columns=str.capitalize)[["Open", "High", "Low", "Close", "Volume"]]


def api_key() -> str:
    return os.environ.get("LSE_API_KEY") or re.search(r"lse_live_\w+", (Path(__file__).parent / "LSE.md").read_text())[0]


def get(path: str, params: dict) -> list[dict]:
    req = urllib.request.Request(f"{VAULT}{path}?{urllib.parse.urlencode(params)}",
                                 headers={"x-api-key": api_key(), "User-Agent": HEADERS_UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def event_labels(rows: list[dict]) -> dict[date, str]:
    """Calendar rows -> {New York date: "FOMC" or "CPI"}, FOMC winning a tie. Rows are read as
    UTC (older ones look like CET), which still gives the right date: releases are 12:30-22:00.
    "Final" rows are the yearly CPI seasonal revision, not a release."""
    labels = {}
    for r in rows:
        name = next((v for k, v in EVENTS.items() if r["event"].startswith(k) and "Final" not in r["event"]), None)
        day = pd.Timestamp(r["datetime"], tz="UTC").tz_convert(MARKET_TZ).date()
        if name and labels.get(day) != "FOMC":
            labels[day] = name
    return labels


def events(start: str = "2016-01-01") -> dict[date, str]:
    """FOMC and CPI days, past and scheduled, refreshed at most once a day."""
    cache = Path("lse_events.json")
    if not cache.exists() or time.time() - cache.stat().st_mtime > 86400:
        rows = [r for e in EVENTS for r in get("/ref/economic_calendar",
                                               {"region": "US", "event": e, "start": start, "limit": 5000})]
        cache.write_text(json.dumps(rows))
    return event_labels(json.loads(cache.read_text()))


def read_cache(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(MARKET_TZ).rename("Datetime")  # mixed EDT/EST offsets
    return df


def fetch(symbol: str = "ES.F", start: str = "2016-01-01") -> pd.DataFrame:
    """All 1h bars since start, cached locally; later calls only download what is new."""
    cache = Path(f"lse_{symbol}_1h.csv")
    old = read_cache(cache) if cache.exists() else None
    if old is not None:
        start = old.index[-1].tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S")
    rows = []
    while True:
        page = get("/candles", {"symbol": symbol, "timeframe": "1h", "start": start, "limit": PAGE, "order": "asc"})
        rows += page
        if len(page) < PAGE:
            break
        start = page[-1]["ts"][:19]  # no microseconds allowed; start is inclusive, the repeat is dropped below
    df = pd.concat([old, to_frame(rows)])
    df = df[~df.index.duplicated(keep="last")]  # the last bar may have been still forming
    df.to_csv(cache)
    return df

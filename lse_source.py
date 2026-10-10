"""Ten years of hourly ES candles from London Strategic Edge (LSE).

Yahoo only serves 1h bars for the last 730 days; the LSE vault has ES.F 1h back to
mid 2016. Needs a free key in the LSE_API_KEY environment variable. The full pull
is ~13 requests of 5000 rows, cached to lse_ES.F_1h.csv; later runs only fetch new bars.
"""

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from app import MARKET_TZ

URL = "https://api.londonstrategicedge.com/vault/candles"
PAGE = 5000  # the API's row cap per request
HEADERS_UA = "caple (+https://github.com/danielbul1/caple)"  # the API refuses Python's default User-Agent


def to_frame(rows: list[dict]) -> pd.DataFrame:
    """API rows (bar-open time in UTC) -> the same New York candles app.py serves."""
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.ts).dt.tz_localize("UTC").dt.tz_convert(MARKET_TZ).rename("Datetime")
    return df.rename(columns=str.capitalize)[["Open", "High", "Low", "Close", "Volume"]]


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
        query = urllib.parse.urlencode({"symbol": symbol, "timeframe": "1h", "start": start,
                                        "limit": PAGE, "order": "asc"})
        req = urllib.request.Request(f"{URL}?{query}", headers={"x-api-key": os.environ["LSE_API_KEY"],
                                                          "User-Agent": HEADERS_UA})
        with urllib.request.urlopen(req, timeout=120) as resp:
            page = json.loads(resp.read())
        rows += page
        if len(page) < PAGE:
            break
        start = page[-1]["ts"][:19]  # no microseconds allowed; start is inclusive, the repeat is dropped below
    df = pd.concat([old, to_frame(rows)])
    df = df[~df.index.duplicated(keep="last")]  # the last bar may have been still forming
    df.to_csv(cache)
    return df

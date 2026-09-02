import io
import requests
import pandas as pd

from . import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _fetch_symbol_csv(url: str, symbol_col_candidates=("Symbol", "SYMBOL")) -> list:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    col = next((c for c in symbol_col_candidates if c in df.columns), None)
    if col is None:
        raise ValueError(f"No recognizable symbol column in {url} (got columns: {list(df.columns)})")
    symbols = df[col].dropna().astype(str).str.strip().tolist()
    return [f"{s}.NS" for s in symbols]


def get_nifty_total_market_symbols() -> list:
    return _fetch_symbol_csv(config.NIFTY_TOTAL_MARKET_URL)


def get_nifty500_symbols() -> list:
    return _fetch_symbol_csv(config.NIFTY500_URL)


def get_all_nse_symbols() -> list:
    """Every NSE-listed equity (~2000+). Needs a browser-like session first,
    since this particular NSE endpoint checks for it."""
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    resp = session.get(config.NSE_EQUITY_LIST_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    symbols = df["SYMBOL"].dropna().astype(str).str.strip().tolist()
    return [f"{s}.NS" for s in symbols]


_UNIVERSE_FETCHERS = {
    "total_market": get_nifty_total_market_symbols,
    "nifty500": get_nifty500_symbols,
    "all": get_all_nse_symbols,
}
_FALLBACK_ORDER = ["total_market", "nifty500", "all"]


def get_nse_symbols() -> list:
    order = [config.UNIVERSE] + [u for u in _FALLBACK_ORDER if u != config.UNIVERSE]
    errors = []
    for universe in order:
        fetcher = _UNIVERSE_FETCHERS.get(universe)
        if fetcher is None:
            continue
        try:
            symbols = fetcher()
            if universe != config.UNIVERSE:
                print(f"[warn] '{config.UNIVERSE}' fetch failed, using '{universe}' instead.")
            return symbols
        except Exception as e:
            errors.append(f"{universe}: {e}")

    raise RuntimeError(
        "Could not fetch a stock symbol list from any source. NSE/niftyindices "
        f"occasionally block automated requests. Errors: {'; '.join(errors)}"
    )

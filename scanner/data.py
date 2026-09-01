import yfinance as yf
import pandas as pd

from . import config


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def fetch_daily_bars(tickers: list) -> dict:
    """
    Download daily bars (period=YF_PERIOD) for a batch of tickers.
    Returns {ticker: dataframe} for tickers that returned usable data.
    """
    out = {}
    for chunk in chunked(tickers, config.CHUNK_SIZE):
        try:
            data = yf.download(
                tickers=chunk,
                period=config.YF_PERIOD,
                interval=config.YF_INTERVAL,
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=False,
            )
        except Exception as e:
            print(f"[warn] chunk download failed ({len(chunk)} tickers): {e}")
            continue

        if data is None or data.empty:
            continue

        if len(chunk) == 1:
            t = chunk[0]
            df = data.dropna(how="all")
            if not df.empty:
                out[t] = df
            continue

        for t in chunk:
            try:
                df = data[t].dropna(how="all")
                if not df.empty:
                    out[t] = df
            except (KeyError, TypeError):
                continue

    return out


def fetch_nifty_return_pct(lookback_days: int) -> float:
    """
    Returns the Nifty index's % return over the last `lookback_days`
    trading sessions, used as the benchmark for relative strength.
    """
    df = yf.download(
        tickers=config.NIFTY_INDEX_TICKER,
        period=config.YF_PERIOD,
        interval=config.YF_INTERVAL,
        progress=False,
        auto_adjust=False,
    )
    df = df.dropna(how="all")
    if len(df) <= lookback_days:
        raise RuntimeError("Not enough Nifty index history to compute relative strength.")
    close = df["Close"]
    latest = close.iloc[-1]
    past = close.iloc[-lookback_days - 1]
    return float((latest - past) / past * 100)

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from scanner import config, symbols, data, state as state_store, notifier
from scanner import signals as signal_engine

ICONS = {
    "GOLDEN_CROSS": "✨",
    "MACD_BULLISH_CROSS": "📈",
    "HILEGA_MILEGA": "🔄",
    "RELATIVE_STRENGTH_LEADER": "🏆",
}


def is_market_open() -> bool:
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    if now_ist.weekday() >= 5:  # Sat/Sun
        return False
    start = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    end = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
    return start <= now_ist <= end


def format_alert(ticker: str, sig: dict) -> str:
    clean_symbol = ticker.replace(".NS", "")
    icon = ICONS.get(sig["type"], "🔔")
    label = sig["type"].replace("_", " ").title()
    return f"{icon} <b>{clean_symbol}</b> — {label}\n{sig['detail']}"


def main():
    if not is_market_open():
        print("Market closed (outside 9:15-15:30 IST, Mon-Fri) — skipping run.")
        return

    print("Fetching Nifty index data for relative strength benchmark...")
    nifty_return_pct = data.fetch_nifty_return_pct(config.RELATIVE_STRENGTH_LOOKBACK_DAYS)
    print(f"Nifty {config.RELATIVE_STRENGTH_LOOKBACK_DAYS}-day return: {nifty_return_pct:.2f}%")

    print("Fetching stock symbol list...")
    tickers = symbols.get_nse_symbols()
    print(f"Tracking {len(tickers)} symbols")

    print("Downloading daily bars...")
    price_data = data.fetch_daily_bars(tickers)
    print(f"Got data for {len(price_data)}/{len(tickers)} symbols")

    state = state_store.load_state()
    candidates = []

    for ticker, df in price_data.items():
        for sig in signal_engine.analyze(ticker, df, nifty_return_pct):
            if state_store.should_alert(state, ticker, sig["type"]):
                candidates.append((ticker, sig))

    print(f"{len(candidates)} candidate alert(s) before ranking/cap")

    candidates.sort(key=lambda pair: pair[1].get("strength", 0), reverse=True)
    alerts = candidates[: config.TOP_N_PER_RUN]

    for ticker, sig in alerts:
        state_store.mark_alerted(state, ticker, sig["type"])

    print(f"{len(alerts)} alert(s) selected to send (top {config.TOP_N_PER_RUN})")

    batch = []
    for ticker, sig in alerts:
        batch.append(format_alert(ticker, sig))
        if len(batch) == 15:
            notifier.send_message("\n\n".join(batch))
            batch = []
            time.sleep(1)
    if batch:
        notifier.send_message("\n\n".join(batch))

    state_store.save_state(state)


if __name__ == "__main__":
    main()

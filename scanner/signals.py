import pandas as pd

from . import config
from . import indicators


def analyze(ticker: str, df: pd.DataFrame, nifty_return_pct: float) -> list:
    """
    Look at the latest daily bar for `ticker` and decide whether it
    deserves an alert. Returns a list of signal dicts (possibly empty).
    Only bullish/buy-side signals are detected, to match this project's
    focus on surfacing potential buy opportunities.
    """
    min_bars_needed = max(config.SMA_LONG, config.FIFTY_TWO_WEEK_LOOKBACK_DAYS) + 5
    if df is None or len(df) < min_bars_needed:
        return []

    close = df["Close"].dropna()
    if close.empty:
        return []

    latest_close = close.iloc[-1]
    if latest_close < config.MIN_STOCK_PRICE:
        return []

    avg_daily_volume = df["Volume"].tail(20).mean()
    if pd.isna(avg_daily_volume) or avg_daily_volume < config.MIN_AVG_DAILY_VOLUME:
        return []

    signals = []

    # --- Golden cross: short SMA crosses above long SMA ---
    sma_short = indicators.sma(close, config.SMA_SHORT)
    sma_long = indicators.sma(close, config.SMA_LONG)
    if sma_short.notna().sum() >= 2 and sma_long.notna().sum() >= 2:
        prev_short, prev_long = sma_short.iloc[-2], sma_long.iloc[-2]
        cur_short, cur_long = sma_short.iloc[-1], sma_long.iloc[-1]
        if pd.notna(prev_short) and pd.notna(prev_long):
            if prev_short <= prev_long and cur_short > cur_long:
                pct_gap = (cur_short - cur_long) / cur_long * 100
                signals.append({
                    "type": "GOLDEN_CROSS",
                    "detail": (
                        f"{config.SMA_SHORT}-day SMA ({cur_short:.2f}) crossed above "
                        f"{config.SMA_LONG}-day SMA ({cur_long:.2f})"
                    ),
                    "strength": abs(pct_gap),
                })

    # --- MACD bullish crossover ---
    macd_line, signal_line = indicators.macd(
        close, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL
    )
    if macd_line.notna().sum() >= 2:
        prev_macd, prev_sig = macd_line.iloc[-2], signal_line.iloc[-2]
        cur_macd, cur_sig = macd_line.iloc[-1], signal_line.iloc[-1]
        if pd.notna(prev_macd) and pd.notna(prev_sig):
            if prev_macd <= prev_sig and cur_macd > cur_sig:
                signals.append({
                    "type": "MACD_BULLISH_CROSS",
                    "detail": (
                        f"MACD ({cur_macd:.2f}) crossed above its signal line ({cur_sig:.2f})"
                    ),
                    "strength": abs(cur_macd - cur_sig),
                })

    # --- Hilega Milega (advanced/3-line version): EMA-of-RSI crosses
    # above WMA-of-RSI (bullish momentum shift) ---
    hm_rsi = indicators.rsi(close, config.HM_RSI_PERIOD)
    hm_wma = indicators.wma(hm_rsi, config.HM_WMA_PERIOD)
    hm_ema = indicators.ema(hm_rsi, config.HM_EMA_PERIOD)
    # Guard against a numerical artifact: during a long flat/zero-RSI
    # stretch, the WMA's finite window can empty to exactly 0 faster than
    # the EMA's decaying tail, creating a spurious "crossover" with no
    # real momentum behind it. Require genuine recent variation in RSI.
    rsi_recent_std = hm_rsi.tail(config.HM_WMA_PERIOD).std()
    has_real_variation = pd.notna(rsi_recent_std) and rsi_recent_std > 1.0

    if has_real_variation and hm_ema.notna().sum() >= 2 and hm_wma.notna().sum() >= 2:
        prev_ema, prev_wma = hm_ema.iloc[-2], hm_wma.iloc[-2]
        cur_ema, cur_wma = hm_ema.iloc[-1], hm_wma.iloc[-1]
        if pd.notna(prev_ema) and pd.notna(prev_wma):
            if prev_ema <= prev_wma and cur_ema > cur_wma:
                signals.append({
                    "type": "HILEGA_MILEGA",
                    "detail": (
                        f"EMA({config.HM_EMA_PERIOD}) of RSI({config.HM_RSI_PERIOD}) "
                        f"crossed above its {config.HM_WMA_PERIOD}-period WMA "
                        f"({cur_ema:.1f} > {cur_wma:.1f})"
                    ),
                    "strength": abs(cur_ema - cur_wma),
                })

    # --- Relative strength vs Nifty ---
    lookback = config.RELATIVE_STRENGTH_LOOKBACK_DAYS
    if len(close) > lookback:
        past_close = close.iloc[-lookback - 1]
        if past_close > 0:
            stock_return = (latest_close - past_close) / past_close * 100
            outperformance = stock_return - nifty_return_pct
            if outperformance >= config.RELATIVE_STRENGTH_THRESHOLD_PCT:
                signals.append({
                    "type": "RELATIVE_STRENGTH_LEADER",
                    "detail": (
                        f"Outperformed Nifty by {outperformance:.1f}pts over "
                        f"{lookback} days ({stock_return:.1f}% vs Nifty's "
                        f"{nifty_return_pct:.1f}%)"
                    ),
                    "strength": outperformance,
                })

    # --- Supertrend flip to bullish ---
    st_trend, st_value = indicators.supertrend(
        df, config.SUPERTREND_PERIOD, config.SUPERTREND_MULTIPLIER
    )
    if len(st_trend) >= 2:
        prev_trend, cur_trend = st_trend.iloc[-2], st_trend.iloc[-1]
        if prev_trend == "down" and cur_trend == "up":
            cur_value = st_value.iloc[-1]
            if pd.notna(cur_value) and cur_value > 0:
                pct_above = (latest_close - cur_value) / cur_value * 100
                signals.append({
                    "type": "SUPERTREND_BULLISH_FLIP",
                    "detail": (
                        f"Supertrend flipped bullish (price {latest_close:.2f} "
                        f"vs Supertrend level {cur_value:.2f})"
                    ),
                    "strength": abs(pct_above),
                })

    # --- 52-week high breakout ---
    fifty_two_week_lookback = config.FIFTY_TWO_WEEK_LOOKBACK_DAYS
    if len(df) > fifty_two_week_lookback:
        prior_high = df["High"].iloc[-fifty_two_week_lookback - 1:-1].max()
        if pd.notna(prior_high) and prior_high > 0 and latest_close > prior_high:
            pct_above = (latest_close - prior_high) / prior_high * 100
            signals.append({
                "type": "FIFTY_TWO_WEEK_HIGH",
                "detail": (
                    f"Price {latest_close:.2f} broke above its 52-week high "
                    f"{prior_high:.2f} (+{pct_above:.1f}%)"
                ),
                "strength": pct_above,
            })

    # --- Bollinger Band breakout: close crosses above the upper band ---
    bb_upper, bb_middle, bb_lower = indicators.bollinger_bands(
        close, config.BB_PERIOD, config.BB_STD
    )
    if bb_upper.notna().sum() >= 2:
        prev_close2, prev_upper = close.iloc[-2], bb_upper.iloc[-2]
        cur_upper = bb_upper.iloc[-1]
        if pd.notna(prev_upper) and pd.notna(cur_upper) and cur_upper > 0:
            if prev_close2 <= prev_upper and latest_close > cur_upper:
                pct_above = (latest_close - cur_upper) / cur_upper * 100
                signals.append({
                    "type": "BOLLINGER_BREAKOUT",
                    "detail": (
                        f"Price {latest_close:.2f} closed above the upper "
                        f"Bollinger Band {cur_upper:.2f} (+{pct_above:.1f}%)"
                    ),
                    "strength": pct_above,
                })

    # --- ADX/DI bullish crossover: +DI crosses above -DI with ADX
    # confirming enough trend strength to matter ---
    plus_di, minus_di, adx = indicators.adx_di(df, config.ADX_PERIOD)
    if plus_di.notna().sum() >= 2:
        prev_plus, prev_minus = plus_di.iloc[-2], minus_di.iloc[-2]
        cur_plus, cur_minus, cur_adx = plus_di.iloc[-1], minus_di.iloc[-1], adx.iloc[-1]
        if pd.notna(prev_plus) and pd.notna(prev_minus) and pd.notna(cur_adx):
            if prev_plus <= prev_minus and cur_plus > cur_minus and cur_adx >= config.ADX_THRESHOLD:
                signals.append({
                    "type": "ADX_DI_BULLISH_CROSS",
                    "detail": (
                        f"+DI ({cur_plus:.1f}) crossed above -DI ({cur_minus:.1f}) "
                        f"with ADX {cur_adx:.1f} confirming trend strength"
                    ),
                    "strength": cur_adx,
                })

    return signals

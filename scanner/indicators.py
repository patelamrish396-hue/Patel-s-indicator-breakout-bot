import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def wma(series: pd.Series, window: int) -> pd.Series:
    """Linearly weighted moving average -- most recent bar gets the
    highest weight, oldest bar in the window gets weight 1."""
    weights = list(range(1, window + 1))
    total_weight = sum(weights)

    def _weighted(x):
        return (x * weights).sum() / total_weight

    return series.rolling(window).apply(_weighted, raw=True)


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Standard Wilder's RSI, computed via an equivalent exponential moving
    average (alpha = 1/period) of gains and losses.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi_val = 100 - (100 / (1 + rs))
    # When there are no losses in the window, RSI should read 100 (maxed
    # out) rather than NaN -- pandas gives inf for the division which
    # already resolves correctly, but guard explicitly for clarity.
    rsi_val = rsi_val.where(avg_loss != 0, 100)
    return rsi_val


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Returns (macd_line, signal_line)."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["Close"].shift(1)
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - prev_close).abs()
    tr3 = (df["Low"] - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range via Wilder-style smoothing (approximated with
    an EMA of alpha=1/period, the same convention used for RSI above)."""
    tr = true_range(df)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    """
    Returns (trend, value) where trend is a Series of 'up'/'down' strings
    and value is the corresponding Supertrend line level at each bar.
    This is inherently a stateful/recursive calculation (each bar depends
    on the previous one's bands and trend), so it's computed in a loop
    rather than vectorized -- fine at daily-bar scale (a few hundred rows).
    """
    atr_val = atr(df, period)
    hl2 = (df["High"] + df["Low"]) / 2
    basic_upper = hl2 + multiplier * atr_val
    basic_lower = hl2 - multiplier * atr_val

    final_upper = pd.Series(index=df.index, dtype=float)
    final_lower = pd.Series(index=df.index, dtype=float)
    trend = pd.Series(index=df.index, dtype=object)
    value = pd.Series(index=df.index, dtype=float)
    close = df["Close"]

    seeded = False
    for i in range(len(df)):
        if pd.isna(atr_val.iloc[i]):
            # Still in the ATR warmup period -- nothing meaningful to compute yet.
            trend.iloc[i] = "up"
            value.iloc[i] = float("nan")
            continue

        if not seeded:
            # First bar with a valid ATR: bootstrap the bands directly.
            # There's no valid previous final_upper/final_lower to ratchet
            # from yet -- comparing against NaN here would silently break
            # the ratchet logic for the rest of the series.
            final_upper.iloc[i] = basic_upper.iloc[i]
            final_lower.iloc[i] = basic_lower.iloc[i]
            trend.iloc[i] = "up"
            value.iloc[i] = final_lower.iloc[i]
            seeded = True
            continue

        if basic_upper.iloc[i] < final_upper.iloc[i - 1] or close.iloc[i - 1] > final_upper.iloc[i - 1]:
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i - 1]

        if basic_lower.iloc[i] > final_lower.iloc[i - 1] or close.iloc[i - 1] < final_lower.iloc[i - 1]:
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i - 1]

        if trend.iloc[i - 1] == "up":
            trend.iloc[i] = "down" if close.iloc[i] < final_lower.iloc[i] else "up"
        else:
            trend.iloc[i] = "up" if close.iloc[i] > final_upper.iloc[i] else "down"

        value.iloc[i] = final_lower.iloc[i] if trend.iloc[i] == "up" else final_upper.iloc[i]

    return trend, value


def adx_di(df: pd.DataFrame, period: int = 14):
    """Returns (plus_di, minus_di, adx), Wilder's directional movement
    system approximated with EMA smoothing (same convention as RSI/ATR)."""
    high = df["High"]
    low = df["Low"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(
        ((up_move > down_move) & (up_move > 0)).astype(float) * up_move.clip(lower=0),
        index=df.index,
    )
    minus_dm = pd.Series(
        ((down_move > up_move) & (down_move > 0)).astype(float) * down_move.clip(lower=0),
        index=df.index,
    )

    smoothed_tr = atr(df, period)  # ATR is just Wilder-smoothed TR
    smoothed_plus_dm = plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    smoothed_minus_dm = minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    plus_di = 100 * (smoothed_plus_dm / smoothed_tr)
    minus_di = 100 * (smoothed_minus_dm / smoothed_tr)

    di_sum = (plus_di + minus_di).replace(0, float("nan"))
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    return plus_di, minus_di, adx


def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0):
    """Returns (upper, middle, lower) bands."""
    middle = sma(series, period)
    std = series.rolling(period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower

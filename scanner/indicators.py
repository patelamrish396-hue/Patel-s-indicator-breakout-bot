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

import os

# --- Universe ---
# Same real, verified NSE index sources as the breakout bot.
# There is no official "Nifty 1000" -- NSE's real lineup is Nifty 500 (500) ->
# Nifty Total Market (750, = Nifty 500 + Nifty Microcap 250) -> every listed
# equity (~2000+).
NIFTY_TOTAL_MARKET_URL = "https://niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv"
NIFTY500_URL = "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv"
NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
# "all" (~2000+), "total_market" (~750), or "nifty500" (~500)
UNIVERSE = os.environ.get("UNIVERSE", "all")

# --- Index used for relative strength comparisons ---
NIFTY_INDEX_TICKER = "^NSEI"

# --- List-length / noise controls (same philosophy as the breakout bot) ---
MIN_STOCK_PRICE = float(os.environ.get("MIN_STOCK_PRICE", 20))
MIN_AVG_DAILY_VOLUME = float(os.environ.get("MIN_AVG_DAILY_VOLUME", 2500))
TOP_N_PER_RUN = int(os.environ.get("TOP_N_PER_RUN", 15))

# --- Indicator settings ---
SMA_SHORT = int(os.environ.get("SMA_SHORT", 50))
SMA_LONG = int(os.environ.get("SMA_LONG", 200))
# --- Hilega Milega (RSI crossing its own WMA) -- popularized by Nitish
# Kumar, widely used by Indian retail traders. Standard defaults are
# RSI(9), WMA(21), and EMA(3) all computed on the RSI. This bot triggers
# on the EMA-of-RSI crossing above the WMA-of-RSI (the "advanced" 3-line
# version of the indicator). ---
HM_RSI_PERIOD = int(os.environ.get("HM_RSI_PERIOD", 9))
HM_WMA_PERIOD = int(os.environ.get("HM_WMA_PERIOD", 21))
HM_EMA_PERIOD = int(os.environ.get("HM_EMA_PERIOD", 3))
MACD_FAST = int(os.environ.get("MACD_FAST", 12))
MACD_SLOW = int(os.environ.get("MACD_SLOW", 26))
MACD_SIGNAL = int(os.environ.get("MACD_SIGNAL", 9))
RELATIVE_STRENGTH_LOOKBACK_DAYS = int(os.environ.get("RELATIVE_STRENGTH_LOOKBACK_DAYS", 20))
RELATIVE_STRENGTH_THRESHOLD_PCT = float(os.environ.get("RELATIVE_STRENGTH_THRESHOLD_PCT", 10))

# --- Supertrend -- very popular with Indian retail traders. Standard
# defaults are ATR period 10, multiplier 3. Fires when the trend flips
# from down to up. ---
SUPERTREND_PERIOD = int(os.environ.get("SUPERTREND_PERIOD", 10))
SUPERTREND_MULTIPLIER = float(os.environ.get("SUPERTREND_MULTIPLIER", 3.0))

# --- 52-week high breakout ---
FIFTY_TWO_WEEK_LOOKBACK_DAYS = int(os.environ.get("FIFTY_TWO_WEEK_LOOKBACK_DAYS", 252))

# --- Bollinger Bands breakout ---
BB_PERIOD = int(os.environ.get("BB_PERIOD", 20))
BB_STD = float(os.environ.get("BB_STD", 2.0))

# --- ADX/DI bullish crossover -- ADX_THRESHOLD requires a minimum trend
# strength at the crossover, to avoid firing in a weak/choppy market. ---
ADX_PERIOD = int(os.environ.get("ADX_PERIOD", 14))
ADX_THRESHOLD = float(os.environ.get("ADX_THRESHOLD", 20))

# --- Data fetching (daily bars -- these signals are computed on daily
# closes, so we don't need intraday data at all, which keeps this much
# lighter than the breakout bot's 15m-bar pipeline) ---
# 400 calendar days, not 300 -- the 52-week high needs ~252 *trading* days
# of history, and 300 calendar days only yields ~205-210 trading days once
# weekends/holidays are excluded.
YF_PERIOD = os.environ.get("YF_PERIOD", "400d")
YF_INTERVAL = "1d"
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 150))

# --- Dedup / cooldown ---
# Daily-timeframe signals don't change more than once a day, so the
# cooldown defaults much longer than the breakout bot's to avoid repeating
# the same signal every 30 minutes through the trading day.
COOLDOWN_MINUTES = int(os.environ.get("COOLDOWN_MINUTES", 1440))
STATE_FILE = "state.json"

# --- Telegram (separate bot/chat from the breakout scanner) ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

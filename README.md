# NSE Technical Signals Telegram Bot

A separate bot from the breakout/volume/pattern scanner — this one focuses
on classic **daily-timeframe technical indicators** used for buy-side stock
screening:

- ✨ **Golden cross** — 50-day SMA crosses above the 200-day SMA (classic
  long-term bullish signal)
- 📈 **MACD bullish crossover** — MACD line crosses above its signal line
  (momentum turning up)
- 🔄 **Hilega Milega** — the EMA-of-RSI crosses above the WMA-of-RSI (a
  popular retail-trader momentum setup, credited to Nitish Kumar; the
  "advanced" 3-line version, using RSI(9), WMA(21), and EMA(3))
- 🏆 **Relative strength leader** — the stock has outperformed the Nifty
  index by a wide margin over the last N trading days

Only **bullish/buy-side signals** are included, matching the same design
choice as the breakout bot. Bearish mirror-images (death cross, MACD
turning down, RSI crossing below its WMA) aren't implemented here, but
could be added.

## ⚠️ Read this first

- **These are daily-timeframe signals.** They're computed from daily
  closing prices, not intraday bars, so they don't change more than once
  per trading day. The bot still checks every 30 minutes (so you find out
  soon after a signal appears, rather than waiting for market close), but
  the built-in cooldown (`COOLDOWN_MINUTES`, default 1440 = 24h) stops you
  from getting the same signal repeated all day.
- **This is a screening tool, not investment advice.** These indicators
  are momentum/trend signals with a long history of false positives —
  they tell you "worth a look," not "buy now." Verify anything before
  acting on it.
- **Free data source (yfinance), same caveats as the breakout bot** apply:
  possible rate-limiting on the full NSE universe, occasional lag, no
  guarantee of accuracy.

## Setup

### 1. Create a *second*, separate Telegram bot
Message [@BotFather](https://t.me/BotFather), send `/newbot`, and create a
new bot distinct from your breakout-scanner bot (so the two alert streams
don't mix). Get its token, message it once, and get your chat ID from
[@userinfobot](https://t.me/userinfobot) (same chat ID works if you're
using the same personal chat for both bots).

### 2. Push this project to a new GitHub repo
```bash
cd nse-technical-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 3. Add secrets
**Settings → Secrets and variables → Actions → New repository secret**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 4. Enable Actions
Go to the **Actions** tab and enable workflows if prompted. It runs
automatically every 30 min on weekdays during market hours. Use
**Run workflow** to trigger a manual test run.

## Tuning

| Variable | Default | Meaning |
|---|---|---|
| `UNIVERSE` | all | `"all"` (every NSE equity, ~2000+), `"total_market"` (~750), or `"nifty500"` (~500) |
| `MIN_STOCK_PRICE` | 20 | Skip stocks priced below this |
| `MIN_AVG_DAILY_VOLUME` | 2500 | Skip stocks whose average daily volume is below this |
| `TOP_N_PER_RUN` | 15 | Max alerts sent per run, keeping the strongest ones |
| `SMA_SHORT` / `SMA_LONG` | 50 / 200 | Moving average pair for the golden cross |
| `HM_RSI_PERIOD` | 9 | RSI period used for Hilega Milega |
| `HM_WMA_PERIOD` | 21 | WMA period applied to that RSI for Hilega Milega |
| `HM_EMA_PERIOD` | 3 | EMA period applied to that RSI; signal fires when this EMA crosses above the WMA |
| `MACD_FAST` / `MACD_SLOW` / `MACD_SIGNAL` | 12 / 26 / 9 | Standard MACD parameters |
| `RELATIVE_STRENGTH_LOOKBACK_DAYS` | 20 | Trading days used to compare stock vs Nifty return |
| `RELATIVE_STRENGTH_THRESHOLD_PCT` | 10 | Minimum outperformance (percentage points) vs Nifty to alert |
| `COOLDOWN_MINUTES` | 1440 | Don't re-alert the same stock+signal within this window (default: once/day) |
| `CHUNK_SIZE` | 150 | Tickers per yfinance batch request |
| `YF_PERIOD` | 300d | Days of daily history pulled per run (must stay above `SMA_LONG`) |

## Local testing

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=xxx
export TELEGRAM_CHAT_ID=xxx
python main.py
```

## Project structure

```
main.py                  # entry point, market-hours check, orchestration
scanner/
  config.py               # thresholds & settings
  symbols.py              # fetches stock universe (Nifty 500/Total Market/all NSE)
  data.py                 # daily-bar downloads + Nifty index fetch
  indicators.py            # SMA, EMA, RSI, MACD math
  signals.py               # golden cross / MACD / RSI / relative strength detection
  state.py                 # cooldown/dedup persisted to state.json
  notifier.py               # Telegram sending
.github/workflows/scan.yml # the cron schedule
state.json                 # committed automatically to remember past alerts
```

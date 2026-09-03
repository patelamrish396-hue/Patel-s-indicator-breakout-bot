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
- 🟢 **Supertrend bullish flip** — the Supertrend indicator (ATR-based
  trend-follower, very popular with Indian retail traders) flips from a
  downtrend to an uptrend
- 🌟 **52-week high breakout** — price closes above its highest price in
  the last ~252 trading days
- 🔔 **Bollinger Band breakout** — price closes above its upper Bollinger
  Band (20-period, 2 standard deviations)
- 💪 **ADX/DI bullish crossover** — +DI crosses above -DI while ADX
  confirms sufficient trend strength (default threshold: 20), filtering
  out crossovers in weak/choppy markets

Only **bullish/buy-side signals** are included, matching the same design
choice as the breakout bot. Bearish mirror-images (death cross, MACD
turning down, RSI crossing below its WMA) aren't implemented here, but
could be added.

## ⚠️ Read this first

- **These are daily-timeframe signals.** They're computed from daily
  closing prices, not intraday bars, so they don't change more than once
  per trading day. The bot checks twice a day — 10:30 AM IST (an early
  heads-up, since the daily candle is still forming) and 3:15 PM IST (the
  more reliable check, since it reads a nearly-final daily candle, only 15
  min before close — most relevant if you're using these signals for BTST).
  The built-in cooldown (`COOLDOWN_MINUTES`, default 1440 = 24h) also stops
  the 10:30 and 3:15 checks from double-alerting on the same signal.
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
automatically at 10:30 AM and 3:15 PM IST on weekdays. Use
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
| `SUPERTREND_PERIOD` | 10 | ATR period used for Supertrend |
| `SUPERTREND_MULTIPLIER` | 3.0 | ATR multiplier used for Supertrend bands |
| `FIFTY_TWO_WEEK_LOOKBACK_DAYS` | 252 | Trading days used for the 52-week high check |
| `BB_PERIOD` | 20 | Bollinger Band period |
| `BB_STD` | 2.0 | Bollinger Band width (standard deviations) |
| `ADX_PERIOD` | 14 | ADX/DI lookback period |
| `ADX_THRESHOLD` | 20 | Minimum ADX required at the +DI/-DI crossover to count as a strong-enough trend |
| `COOLDOWN_MINUTES` | 1440 | Don't re-alert the same stock+signal within this window (default: once/day) |
| `CHUNK_SIZE` | 150 | Tickers per yfinance batch request |
| `YF_PERIOD` | 400d | Calendar days of daily history pulled per run (needs to comfortably exceed `FIFTY_TWO_WEEK_LOOKBACK_DAYS` in trading-day terms) |

## Local testing

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=xxx
export TELEGRAM_CHAT_ID=xxx
python main.py
```

## Troubleshooting: scheduled runs missing entirely (works fine on manual "Run workflow")

This is a known GitHub Actions limitation, not a bug in this project.
GitHub's own docs state that scheduled ("cron") triggers are **best
effort**: they can be delayed during high load, and if load is high
enough, **queued runs can be dropped entirely** — with no error anywhere,
since nothing ran at all. The start of every hour and half-hour is
specifically called out as peak load. The two check times here are
nudged a few minutes off round numbers (`5:03`/`9:43` UTC rather than
`5:00`/`9:45`) for exactly this reason.

If missed runs are still frequent enough to matter, the fully reliable
fix (per GitHub's own community threads) is to stop relying on GitHub's
schedule queue at all: use a free external scheduler (e.g. cron-job.org)
to call the [`workflow_dispatch` REST API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
at the exact time you want — it's dispatched near-instantly and doesn't
sit in the same delay-prone queue as `schedule`. Needs a GitHub Personal
Access Token with `actions: write` permission. Happy to help set this up
if the offset-cron fix above isn't enough on its own.

## Project structure

```
main.py                  # entry point, market-hours check, orchestration
scanner/
  config.py               # thresholds & settings
  symbols.py              # fetches stock universe (Nifty 500/Total Market/all NSE)
  data.py                 # daily-bar downloads + Nifty index fetch
  indicators.py            # SMA, EMA, RSI, MACD, ATR, Supertrend, ADX/DI, Bollinger Bands
  signals.py               # golden cross / MACD / Hilega Milega / relative strength /
                            # Supertrend / 52-week high / Bollinger / ADX-DI detection
  state.py                 # cooldown/dedup persisted to state.json
  notifier.py               # Telegram sending
.github/workflows/scan.yml # the cron schedule
state.json                 # committed automatically to remember past alerts
```

# Agentic Crypto Trader — Final Paper Edition

A modular Python intraday crypto research/trading simulator. It uses public Binance Spot data through CCXT, a coordinated set of specialist agents, deterministic technical filters, a risk supervisor, paper execution with fees/slippage, SQLite journaling, and a historical OHLCV backtester.

## Critical boundary
**This distribution is paper-trading only.** It has no authenticated exchange client and no live-order method. `TRADING_MODE` is validated and any value other than `paper` is rejected. No Binance API key is needed for public prices or simulated orders. Real account access or real trading is not part of this release.

No strategy is guaranteed profitable. The strategy and parameters are experimental; paper fills do not reproduce order-book depth, queue priority, exchange latency, market impact, or all failure modes. This is an educational engineering project, not financial advice.

## Architecture
- `MarketScannerAgent`: ranks liquid USDT spot pairs by 24-hour quote volume.
- `StrategyAnalystAgent`: fetches closed candles and evaluates a transparent EMA/RSI/VWAP/volume hypothesis.
- `RiskSupervisorAgent`: deterministically vetoes entries that exceed risk, cash, daily loss or open-position limits.
- `PaperBroker`: simulates spot long entries/exits, fee and slippage assumptions, stop-loss/take-profit and P&L.
- `PerformanceAgent`: emits basic paper portfolio metrics.
- `Journal`: stores trade records and equity snapshots in SQLite.
- `backtest.py`: historical simulation, trades CSV and equity CSV.

“Agentic” here means a coordinated, bounded set of specialist agents. The current release does not depend on an LLM API; that avoids requiring a model key and keeps trade/risk decisions auditable. An optional LLM research/explanation agent can be added later, but it must never override deterministic risk checks.

## Setup (Windows PowerShell, Python 3.10+)
```powershell
cd agentic_crypto_trader_final
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m unittest test_trading_core.py -v
python main.py
```
No API key is required. Internet access is required for current public market data. If Binance public endpoints are unavailable in your region/network, the scanner will not work until a legally accessible supported market-data source is configured.

## Historical backtesting
Download recent public candles from Binance:
```powershell
python backtest.py --download --symbol BTC/USDT --timeframe 5m --limit 1000 --out btc_5m
```
Or provide your own CSV with `timestamp,open,high,low,close,volume` columns:
```powershell
python backtest.py --csv candles.csv --out my_test
```
Outputs: `*_trades.csv` and `*_equity.csv`, plus summary metrics. The built-in fetch is capped to a recent exchange candle window; it is not a full multi-year data pipeline. For research-grade testing, collect larger histories and use train/validation/test splits or walk-forward evaluation.

## Strategy hypothesis (not validated)
Entry uses completed candles and requires all of:
- EMA(9) above EMA(21)
- RSI(14) between 50 and 68
- Close above a rolling-window VWAP approximation
- Volume greater than 1.2 × 20-candle average

Exit: 1.2% stop, 2.4% target. If both stop and target are touched within one OHLC candle, the simulator assumes stop first. Backtest entries are at the next candle open after a signal to reduce look-ahead bias.

## Default risk limits
- Starting paper cash: 100 USDT
- Risk budget: 0.5% equity per trade
- Position notional cap: 25% of equity
- Maximum open positions: 3
- Daily loss threshold: 2% from the UTC-day reference equity, blocks new entries
- Illustrative fees: 0.10% each side; slippage: 0.05% each side

Update the assumptions to match the actual venue fee tier and market conditions before interpreting results. Stops do not guarantee maximum loss in real trading. The daily-loss check is a new-entry lockout, not an exchange-level liquidation or forced liquidation mechanism.

## Files
```text
agentic_crypto_trader_final/
├── main.py
├── config.py
├── market_data.py
├── agents.py
├── strategy.py
├── risk_manager.py
├── paper_broker.py
├── journal.py
├── backtest.py
├── test_trading_core.py
├── requirements.txt
├── .env.example
└── README.md
```

## Limitations to understand
- The rolling VWAP is an approximation over fetched candles, not a true session-reset VWAP.
- The live scanner only examines the most liquid selected pairs; positions can be missed if a symbol drops out of that list, so this build is not a production-grade portfolio manager.
- Open paper positions are held in memory; the SQLite journal persists records, but restarting the program does not restore open position state. Do not interpret restarts as continuous account simulation.
- The current backtester is single-symbol and simplified. It is not yet a portfolio-level, multi-coin walk-forward research system.
- No LLM API, dashboard, Telegram/WhatsApp alerts, or live trading adapter is included in this release.

## Before any future live trading
Build and independently test persistent position recovery, exchange precision/min-notional filters, order reconciliation, idempotency, partial fills, clock skew, websocket disconnect handling, exchange outages, independent kill switch, and least-privilege credentials. Start with exchange testnet/paper simulations and check applicable laws and taxes. Never expose API keys in chat or source control.

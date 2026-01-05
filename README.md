Crypto Intraday Alert Engine (24/7)

A real-time, stateful crypto intraday alert system built using Python.
The system monitors multiple crypto pairs continuously, evaluates high-confidence intraday setups using technical indicators, manages risk per trade, and sends actionable alerts via Telegram.

It also includes a live dashboard for performance tracking and P&L analysis.


Key Features

* Real-time market data using Binance WebSocket (24/7)

* Multi-indicator strategy engine

Trend detection

RSI regime filtering

VWAP bounce confirmation

EMA compression

* Risk management

Fixed USDT capital per trade

Predefined Risk–Reward ratio

Automatic Stop Loss & Target calculation

* Anti-spam logic

Only one active trade per symbol

New alerts only after trade exit (SL / Target)

* Telegram alerts

Entry alerts

Exit alerts (Target / Stop Loss hit)

* Persistent state

SQLite database for system status and active trades

* Trade journal

CSV-based logging with entry, exit, and P&L

* Streamlit dashboard

Live unrealized P&L

Total realized P&L

Win rate

Equity curve
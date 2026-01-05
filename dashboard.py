import streamlit as st
import pandas as pd

from metrics.trade_metrics import compute_metrics
from metrics.open_pnl import get_open_trades_with_pnl
from state_db import get_conn


st.set_page_config(page_title="Crypto Trading Dashboard", layout="wide")
st.title("📊 Crypto Intraday Trading Dashboard")


conn = get_conn()
status_rows = conn.execute("SELECT key, value FROM system_status").fetchall()
conn.close()

status = dict(status_rows)

c1, c2 = st.columns(2)
c1.metric("WebSocket Status", status.get("websocket", "UNKNOWN"))
c2.metric("Last Candle Time", status.get("last_candle_time", "-"))

st.divider()


metrics = compute_metrics()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total P&L (USDT)", metrics["total_pnl"])
m2.metric("Win Rate (%)", metrics["win_rate"])
m3.metric("Total Trades", metrics["total_trades"])
m4.metric("Wins / Losses", f"{metrics['wins']} / {metrics['losses']}")

st.divider()



st.subheader("📈 Equity Curve")

if metrics["equity_curve"]:
    df = pd.DataFrame({"Equity (USDT)": metrics["equity_curve"]})
    st.line_chart(df)
else:
    st.info("No closed trades yet.")

st.divider()


st.subheader("🟢 Open Trades — Live Unrealized P&L")

conn = get_conn()

try:
    rows = conn.execute("SELECT symbol, price FROM last_prices").fetchall()
except Exception:
    rows = []

conn.close()

latest_prices = {s: p for s, p in rows}

open_trades, total_unrealized = get_open_trades_with_pnl(latest_prices)

if open_trades:
    st.dataframe(pd.DataFrame(open_trades), use_container_width=True)
    st.metric("Total Unrealized P&L (USDT)", total_unrealized)
else:
    st.info("No open trades currently.")

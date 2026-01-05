import sqlite3

DB_PATH = "state.db"


def get_open_trades_with_pnl(latest_prices):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        rows = cursor.execute("""
            SELECT symbol, entry, quantity, trend
            FROM active_trades
            WHERE status='OPEN'
        """).fetchall()
    except Exception:
        conn.close()
        return [], 0.0

    conn.close()

    open_trades = []
    total_pnl = 0.0

    for symbol, entry, qty, trend in rows:
        price = latest_prices.get(symbol)
        if price is None:
            continue

        pnl = (price - entry) * qty if trend == "BULLISH" else (entry - price) * qty
        total_pnl += pnl

        open_trades.append({
            "symbol": symbol,
            "entry": entry,
            "price": price,
            "quantity": qty,
            "pnl": round(pnl, 2),
        })

    return open_trades, round(total_pnl, 2)

from state_db import get_conn


def get_open_trades_with_pnl(latest_prices: dict):
    """
    latest_prices = { "BTCUSDT": 43000.5, ... }
    """

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, entry, quantity, trend
        FROM active_trades
        WHERE status='OPEN'
    """)

    rows = cur.fetchall()
    conn.close()

    open_trades = []
    total_unrealized = 0.0

    for symbol, entry, qty, trend in rows:
        current = latest_prices.get(symbol)
        if current is None:
            continue

        pnl = (current - entry) * qty
        total_unrealized += pnl

        open_trades.append({
            "Symbol": symbol,
            "Entry": round(entry, 4),
            "Current": round(current, 4),
            "Quantity": round(qty, 6),
            "PnL (USDT)": round(pnl, 3),
        })

    return open_trades, round(total_unrealized, 3)

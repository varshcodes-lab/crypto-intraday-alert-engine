import sqlite3

DB_PATH = "state.db"


def compute_metrics():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        rows = cur.execute(
            "SELECT result, pnl FROM trades WHERE pnl IS NOT NULL"
        ).fetchall()
    except Exception:
        conn.close()
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "equity_curve": [],
        }

    conn.close()

    total_trades = len(rows)
    wins = sum(1 for r, _ in rows if r == "WIN")
    losses = sum(1 for r, _ in rows if r == "LOSS")
    total_pnl = sum(pnl for _, pnl in rows)

    win_rate = (wins / total_trades * 100) if total_trades else 0

    equity = []
    running = 0
    for _, pnl in rows:
        running += pnl
        equity.append(round(running, 2))

    return {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "equity_curve": equity,
    }

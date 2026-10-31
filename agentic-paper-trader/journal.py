import sqlite3
from contextlib import closing


class Journal:
    def __init__(self, path):
        self.path = path

        with closing(sqlite3.connect(path)) as con:
            con.execute("""CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                qty REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                stop_price REAL NOT NULL,
                target_price REAL NOT NULL,
                entry_fee REAL NOT NULL,
                exit_fee REAL,
                pnl REAL,
                status TEXT NOT NULL,
                reason TEXT
            )""")

            con.execute("""CREATE TABLE IF NOT EXISTS equity_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cash REAL NOT NULL,
                equity REAL NOT NULL
            )""")

            con.execute("""CREATE TABLE IF NOT EXISTS portfolio_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                initial_cash REAL NOT NULL
            )""")

            con.commit()

    def initialize_portfolio(self, initial_cash):
        if initial_cash <= 0:
            raise ValueError("Initial cash must be positive.")

        with closing(sqlite3.connect(self.path)) as con:
            con.execute(
                """INSERT OR IGNORE INTO portfolio_state
                   (id, initial_cash) VALUES (1, ?)""",
                (float(initial_cash),)
            )
            con.commit()

    def add_trade(self, values):
        with closing(sqlite3.connect(self.path)) as con:
            cur = con.execute("""INSERT INTO trades
                (symbol, entry_time, qty, entry_price, stop_price,
                 target_price, entry_fee, status, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)""", values)

            con.commit()
            return int(cur.lastrowid)

    def close_trade(self, trade_id, exit_time, exit_price,
                    exit_fee, pnl, reason):

        with closing(sqlite3.connect(self.path)) as con:
            cur = con.execute(
                """UPDATE trades
                   SET exit_time=?, exit_price=?, exit_fee=?,
                       pnl=?, status='CLOSED', reason=?
                   WHERE id=? AND status='OPEN'""",
                (exit_time, exit_price, exit_fee, pnl, reason, trade_id)
            )

            con.commit()

            if cur.rowcount != 1:
                raise ValueError(
                    f"Trade {trade_id} was not found as an open trade."
                )

    def get_open_trades(self):
        with closing(sqlite3.connect(self.path)) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM trades WHERE status='OPEN' ORDER BY id"
            ).fetchall()
            return [dict(row) for row in rows]

    def get_closed_trades(self):
        with closing(sqlite3.connect(self.path)) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM trades WHERE status='CLOSED' ORDER BY id"
            ).fetchall()
            return [dict(row) for row in rows]

    def load_portfolio(self):
        with closing(sqlite3.connect(self.path)) as con:
            con.row_factory = sqlite3.Row

            state = con.execute(
                "SELECT initial_cash FROM portfolio_state WHERE id=1"
            ).fetchone()

            if state is None:
                raise RuntimeError(
                    "Portfolio not initialized. Call initialize_portfolio first."
                )

            initial_cash = float(state["initial_cash"])
            cash = initial_cash
            realized_pnl = 0.0
            closed_trades = 0
            wins = 0
            losses = 0
            positions = {}

            rows = con.execute(
                "SELECT * FROM trades ORDER BY id"
            ).fetchall()

            for row in rows:
                trade = dict(row)

                symbol = trade["symbol"]
                qty = float(trade["qty"])
                entry = float(trade["entry_price"])
                entry_fee = float(trade["entry_fee"])

                cash -= qty * entry + entry_fee

                if trade["status"] == "OPEN":
                    if symbol in positions:
                        raise RuntimeError(
                            f"Multiple open trades found for {symbol}."
                        )
                    positions[symbol] = trade

                elif trade["status"] == "CLOSED":
                    if trade["exit_price"] is None:
                        raise RuntimeError(
                            f"Closed trade {trade['id']} has no exit price."
                        )

                    exit_price = float(trade["exit_price"])
                    exit_fee = float(trade["exit_fee"] or 0.0)
                    pnl = float(trade["pnl"] or 0.0)

                    cash += qty * exit_price - exit_fee
                    realized_pnl += pnl
                    closed_trades += 1

                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1

                else:
                    raise RuntimeError(
                        f"Unknown trade status: {trade['status']}"
                    )

            if cash < -0.000001:
                raise RuntimeError(
                    f"Reconstructed cash is negative: {cash:.8f}"
                )

            return {
                "initial_cash": initial_cash,
                "cash": max(0.0, cash),
                "positions": positions,
                "realized_pnl": realized_pnl,
                "closed_trades": closed_trades,
                "wins": wins,
                "losses": losses
            }

    def snapshot(self, timestamp, cash, equity):
        with closing(sqlite3.connect(self.path)) as con:
            con.execute(
                """INSERT INTO equity_snapshots
                   (timestamp, cash, equity) VALUES (?, ?, ?)""",
                (timestamp, cash, equity)
            )
            con.commit()

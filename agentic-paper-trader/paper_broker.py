from dataclasses import dataclass
from datetime import datetime, timezone
from journal import Journal


@dataclass
class Position:
    trade_id: int
    symbol: str
    qty: float
    entry_price: float
    stop_price: float
    target_price: float
    entry_fee: float
    entry_time: str


class PaperBroker:
    def __init__(self, initial_cash, fee_rate, slippage_rate, journal: Journal):
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.journal = journal

        # Initialize only once; the database retains the original capital.
        self.journal.initialize_portfolio(initial_cash)
        state = self.journal.load_portfolio()

        self.cash = state["cash"]
        self.realized_pnl = state["realized_pnl"]
        self.closed_trades = state["closed_trades"]
        self.wins = state["wins"]
        self.losses = state["losses"]

        # Reconstruct open Position objects from the persisted trade ledger.
        self.positions = {}

        for symbol, trade in state["positions"].items():
            self.positions[symbol] = Position(
                trade_id=int(trade["id"]),
                symbol=trade["symbol"],
                qty=float(trade["qty"]),
                entry_price=float(trade["entry_price"]),
                stop_price=float(trade["stop_price"]),
                target_price=float(trade["target_price"]),
                entry_fee=float(trade["entry_fee"]),
                entry_time=trade["entry_time"]
            )

    def equity(self, marks):
        return self.cash + sum(
            p.qty * marks.get(symbol, p.entry_price)
            for symbol, p in self.positions.items()
        )

    def enter_long(self, symbol, qty, reference_price,
                   stop_pct, target_pct, reason):

        if symbol in self.positions or qty <= 0 or reference_price <= 0:
            return False

        fill = reference_price * (1 + self.slippage_rate)
        qty = min(qty, self.cash / (fill * (1 + self.fee_rate)))

        notional = qty * fill
        fee = notional * self.fee_rate
        total = notional + fee

        if qty <= 0 or total > self.cash:
            return False

        now = datetime.now(timezone.utc).isoformat()
        stop = fill * (1 - stop_pct)
        target = fill * (1 + target_pct)

        tid = self.journal.add_trade(
            (symbol, now, qty, fill, stop, target, fee, reason)
        )

        self.cash -= total
        self.positions[symbol] = Position(
            tid, symbol, qty, fill, stop, target, fee, now
        )

        print(
            f"[PAPER BUY] {symbol} qty={qty:.8f} "
            f"fill={fill:.8f} stop={stop:.8f} "
            f"target={target:.8f} fee={fee:.5f}"
        )
        return True

    def evaluate_exit(self, symbol, candle):
        p = self.positions.get(symbol)

        if not p:
            return False

        low = float(candle["low"])
        high = float(candle["high"])

        # Conservative, gap-aware exits. Stop takes priority if both levels are touched.
        candle_open = float(candle.get("open", p.stop_price))

        if low <= p.stop_price:
            why, reference = "stop_loss", min(p.stop_price, candle_open)
        elif high >= p.target_price:
            why, reference = "take_profit", max(p.target_price, candle_open)
        else:
            return False

        fill = reference * (1 - self.slippage_rate)
        gross = p.qty * fill
        fee = gross * self.fee_rate

        pnl = (gross - fee) - (p.qty * p.entry_price + p.entry_fee)

        # Persist the close before mutating in-memory portfolio state.
        self.journal.close_trade(
            p.trade_id,
            datetime.now(timezone.utc).isoformat(),
            fill,
            fee,
            pnl,
            why
        )

        self.cash += gross - fee
        self.realized_pnl += pnl
        self.closed_trades += 1

        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1

        del self.positions[symbol]

        print(
            f"[PAPER SELL] {symbol} reason={why} "
            f"fill={fill:.8f} net_pnl={pnl:.5f} USDT"
        )
        return True

from dataclasses import dataclass

@dataclass
class RiskManager:
    risk_per_trade: float
    max_daily_loss: float
    max_position_fraction: float
    max_open_positions: int
    stop_loss_pct: float

    def position_quantity(self, equity, cash, entry_price, open_positions,
                          daily_start_equity, current_equity):
        if min(equity, cash, entry_price) <= 0: return 0.0, "invalid_equity_cash_or_price"
        if open_positions >= self.max_open_positions: return 0.0, "max_open_positions"
        if daily_start_equity > 0 and current_equity <= daily_start_equity * (1-self.max_daily_loss):
            return 0.0, "daily_loss_limit_reached"
        risk_budget = equity * self.risk_per_trade
        per_unit_risk = entry_price * self.stop_loss_pct
        qty_risk = risk_budget / per_unit_risk
        qty_notional = equity * self.max_position_fraction / entry_price
        # Cash buffer for estimated fee; broker additionally enforces cash.
        qty_cash = cash / (entry_price * 1.002)
        qty = max(0.0, min(qty_risk, qty_notional, qty_cash))
        return (qty, "approved") if qty > 0 else (0.0, "position_size_zero")

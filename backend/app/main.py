from __future__ import annotations

from typing import Any


class DemoPaperTrading:
    def __init__(self, starting_balance: float = 10000.0, currency: str = "INR"):
        self.starting_balance = float(starting_balance)
        self.balance = float(starting_balance)
        self.currency = currency
        self.positions: list[dict[str, Any]] = []
        self.trade_history: list[dict[str, Any]] = []

    def open_position(self, market: str, side: str, quantity: float, entry_price: float, timeframe: str = "15m") -> dict[str, Any]:
        side = side.upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError("Side must be BUY or SELL for demo trading.")
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        position = {
            "market": market,
            "side": side,
            "quantity": float(quantity),
            "entry_price": float(entry_price),
            "timeframe": timeframe,
            "demo": True,
        }
        self.positions.append(position)
        return position

    def close_position(self, market: str, exit_price: float, reason: str = "manual close") -> dict[str, Any]:
        matching = next((position for position in self.positions if position["market"] == market), None)
        if matching is None:
            raise ValueError(f"No open demo position for {market}.")

        pnl = (exit_price - matching["entry_price"]) * matching["quantity"] if matching["side"] == "BUY" else (matching["entry_price"] - exit_price) * matching["quantity"]
        self.balance += pnl
        trade = {
            "market": market,
            "pnl": float(pnl),
            "exit_price": float(exit_price),
            "currency": self.currency,
            "demo": True,
            "reason": reason,
        }
        self.trade_history.append(trade)
        self.positions = [position for position in self.positions if position["market"] != market]
        return trade

    def get_summary(self) -> dict[str, Any]:
        return {
            "currency": self.currency,
            "starting_balance": float(self.starting_balance),
            "current_balance": float(self.balance),
            "open_positions": len(self.positions),
            "demo_only": True,
            "trade_history": self.trade_history,
        }


__all__ = ["DemoPaperTrading"]

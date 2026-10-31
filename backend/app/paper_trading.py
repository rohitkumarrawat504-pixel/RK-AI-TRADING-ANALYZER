from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.analysis import analyze_market


def run_backtest(
    candles: pd.DataFrame,
    initial_balance: float = 10000.0,
    spread: float = 0.0008,
    slippage: float = 0.0005,
    market_symbol: str = "BTC-USD",
    timeframe: str = "15m",
) -> dict[str, Any]:
    if candles.empty:
        raise ValueError("Cannot backtest with empty candle data.")
    if len(candles) < 40:
        raise ValueError("Need more candles to produce a meaningful backtest sample.")

    df = candles.copy().reset_index(drop=True)
    balance = float(initial_balance)
    position = 0.0
    entry_price = 0.0
    trade_history: list[dict[str, Any]] = []
    pnl_history: list[float] = [balance]
    peak_balance = balance
    max_drawdown = 0.0
    wins = 0
    losses = 0

    for idx in range(40, len(df)):
        window = df.iloc[max(0, idx - 30): idx + 1].copy()
        analysis = analyze_market(window, market_symbol=market_symbol, timeframe=timeframe)
        signal = analysis["signal"]
        close = float(df.iloc[idx]["close"])

        if signal == "BUY" and position == 0:
            entry_price = close * (1 + spread + slippage)
            position = balance * 0.25 / entry_price
            trade_history.append({"entry_index": idx, "side": "BUY", "price": entry_price, "position": position})
        elif signal == "SELL" and position > 0:
            exit_price = close * (1 - spread - slippage)
            pnl = (exit_price - entry_price) * position
            balance += pnl
            if pnl > 0:
                wins += 1
            else:
                losses += 1
            trade_history[-1]["exit_price"] = exit_price
            trade_history[-1]["pnl"] = pnl
            trade_history[-1]["status"] = "closed"
            position = 0.0
            pnl_history.append(balance)
            peak_balance = max(peak_balance, balance)
            max_drawdown = max(max_drawdown, (peak_balance - balance) / peak_balance if peak_balance else 0.0)
        elif signal == "WAIT" and position > 0:
            exit_price = close * (1 - spread - slippage)
            pnl = (exit_price - entry_price) * position
            balance += pnl
            trade_history[-1]["exit_price"] = exit_price
            trade_history[-1]["pnl"] = pnl
            trade_history[-1]["status"] = "closed"
            position = 0.0
            if pnl > 0:
                wins += 1
            else:
                losses += 1
            pnl_history.append(balance)
            peak_balance = max(peak_balance, balance)
            max_drawdown = max(max_drawdown, (peak_balance - balance) / peak_balance if peak_balance else 0.0)

    if position > 0:
        exit_price = float(df.iloc[-1]["close"]) * (1 - spread - slippage)
        pnl = (exit_price - entry_price) * position
        balance += pnl
        trade_history.append({"side": "BUY", "status": "closed_at_end", "pnl": pnl, "exit_price": exit_price})
        if pnl > 0:
            wins += 1
        else:
            losses += 1
        pnl_history.append(balance)

    total_return = (balance - initial_balance) / initial_balance if initial_balance else 0.0
    win_rate = (wins / (wins + losses)) if (wins + losses) else 0.0
    result = {
        "market_symbol": market_symbol,
        "timeframe": timeframe,
        "initial_balance": float(initial_balance),
        "final_balance": float(balance),
        "total_return": float(total_return),
        "total_return_pct": float(total_return * 100.0),
        "win_rate": float(win_rate),
        "wins": wins,
        "losses": losses,
        "max_drawdown": float(max_drawdown * 100.0),
        "sample_size": int(len(df)),
        "out_of_sample_validation": "Not a guarantee of future performance; used as a research evaluation only.",
        "transaction_cost_assumption": {
            "spread": spread,
            "slippage": slippage,
            "cost_model": "Simplified spread + slippage assumptions for educational backtesting only.",
        },
        "trade_history": trade_history,
    }
    return result


__all__ = ["run_backtest"]

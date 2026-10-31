import pandas as pd

from app.backtesting import run_backtest


def sample_candles():
    rows = []
    price = 100
    for i in range(80):
        open_ = price
        close = price + (1 if i % 3 else -1)
        high = max(open_, close) + 2
        low = min(open_, close) - 2
        volume = 1000 + i * 10
        rows.append({"timestamp": pd.Timestamp.utcnow() + pd.Timedelta(minutes=i), "open": open_, "high": high, "low": low, "close": close, "volume": volume})
        price = close
    return pd.DataFrame(rows)


def test_backtest_returns_summary():
    df = sample_candles()
    result = run_backtest(df, initial_balance=10000, market_symbol="BTC-USD", timeframe="15m")
    assert "final_balance" in result
    assert "win_rate" in result
    assert "max_drawdown" in result
    assert "sample_size" in result

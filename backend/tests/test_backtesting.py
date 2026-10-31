import pandas as pd

from app.analysis import analyze_market


def build_bullish_df():
    prices = [
        100, 101, 103, 104, 105, 108, 110, 112, 114, 116,
        118, 120, 122, 124, 126, 128, 130, 132, 135, 138,
        141, 144, 146, 148, 150, 152, 155, 158, 160, 163,
        166, 169, 172, 175, 178, 180, 182, 185, 188, 190,
    ]
    data = []
    for i, close in enumerate(prices):
        open_ = close - 1.5
        high = close + 2
        low = close - 2
        volume = 1000 + i * 20
        data.append({"open": open_, "high": high, "low": low, "close": close, "volume": volume})
    return pd.DataFrame(data)


def test_bullish_signal_logic():
    df = build_bullish_df()
    analysis = analyze_market(df, market_symbol="BTC-USD", timeframe="15m")
    assert analysis["signal"] in {"BUY", "SELL", "WAIT"}
    assert "reasons" in analysis
    assert "support" in analysis
    assert "resistance" in analysis

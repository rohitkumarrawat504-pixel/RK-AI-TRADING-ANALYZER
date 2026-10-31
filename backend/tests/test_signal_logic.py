import pandas as pd

from app.indicators import compute_indicators, candle_summary


def build_sample_df():
    return pd.DataFrame(
        {
            "open": [100, 101, 103, 104, 105, 101, 102, 104, 106, 110],
            "high": [101, 103, 104, 106, 109, 103, 104, 107, 109, 112],
            "low": [99, 100, 102, 103, 100, 99, 101, 103, 105, 108],
            "close": [101, 103, 104, 105, 103, 102, 103, 106, 109, 111],
            "volume": [1200, 1300, 1700, 1800, 2100, 1500, 1800, 2000, 2300, 2400],
        }
    )


def test_compute_indicators():
    df = build_sample_df()
    result = compute_indicators(df)
    assert "ema_9" in result.columns
    assert "rsi_14" in result.columns
    assert "macd_hist" in result.columns
    assert "atr_14" in result.columns


def test_candle_summary():
    df = build_sample_df()
    summary = candle_summary(df)
    assert "bullish_candles" in summary
    assert "bearish_candles" in summary
    assert "doji_count" in summary

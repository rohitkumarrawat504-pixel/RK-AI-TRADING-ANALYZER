from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).fillna(0)
    loss = (-delta.clip(upper=0)).fillna(0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_12 = ema(series, 12)
    ema_26 = ema(series, 26)
    macd_line = ema_12 - ema_26
    signal_line = ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    true_range = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False).mean()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    result = df.copy()
    result["ema_9"] = ema(result["close"], 9)
    result["ema_21"] = ema(result["close"], 21)
    result["ema_50"] = ema(result["close"], 50)
    result["rsi_14"] = rsi(result["close"], 14)
    result["macd_line"], result["macd_signal"], result["macd_hist"] = macd(result["close"])
    result["atr_14"] = atr(result["high"], result["low"], result["close"], 14)
    result["volatility"] = (result["high"] - result["low"]) / result["close"].replace(0, np.nan)
    result["volume_change"] = result["volume"].pct_change().fillna(0)
    result["bullish_candle"] = (result["close"] >= result["open"]) & ((result["close"] - result["open"]) > 0)
    result["bearish_candle"] = (result["close"] < result["open"]) & ((result["open"] - result["close"]) > 0)
    result["doji"] = (result["high"] - result["low"]) > 0
    result["doji"] = result["doji"] & ((result["close"] - result["open"]).abs() / (result["high"] - result["low"]).replace(0, np.nan) < 0.1)
    result["candle_body"] = (result["close"] - result["open"]).abs()
    return result


def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> dict[str, float | Any]:
    if df.empty:
        return {"support": None, "resistance": None, "support_zone": None, "resistance_zone": None}
    recent = df.tail(window)
    support = recent["low"].min()
    resistance = recent["high"].max()
    return {
        "support": float(support),
        "resistance": float(resistance),
        "support_zone": float(support * 0.998),
        "resistance_zone": float(resistance * 1.002),
    }


def detect_pattern(row: pd.Series) -> str:
    body = row["close"] - row["open"]
    upper_wick = row["high"] - max(row["open"], row["close"])
    lower_wick = min(row["open"], row["close"]) - row["low"]

    if abs(body) < 0.02 * max(row["high"] - row["low"], 1e-8):
        return "doji"
    if body > 0 and lower_wick > upper_wick * 1.5:
        return "hammer"
    if body < 0 and upper_wick > lower_wick * 1.5:
        return "shooting_star"
    return "neutral"


def candle_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"bullish_candles": 0, "bearish_candles": 0, "doji_count": 0, "engulfing_count": 0}
    summary = {
        "bullish_candles": int((df["close"] >= df["open"]).sum()),
        "bearish_candles": int((df["close"] < df["open"]).sum()),
        "doji_count": int(df["doji"].sum()),
    }
    engulfing = 0
    for idx in range(1, len(df)):
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]
        prev_body = prev["close"] - prev["open"]
        curr_body = curr["close"] - curr["open"]
        if prev_body * curr_body < 0 and abs(curr_body) > abs(prev_body):
            engulfing += 1
    summary["engulfing_count"] = engulfing
    return summary


__all__ = [
    "ema",
    "rsi",
    "macd",
    "atr",
    "compute_indicators",
    "calculate_support_resistance",
    "detect_pattern",
    "candle_summary",
]

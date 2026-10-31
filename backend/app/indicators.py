from __future__ import annotations

from typing import Any

import pandas as pd

from app.indicators import calculate_support_resistance, candle_summary, compute_indicators, detect_pattern


def determine_trend(last_close: float, ema_9: float, ema_21: float, ema_50: float) -> str:
    if last_close > ema_9 > ema_21 > ema_50:
        return "Bullish trend"
    if last_close < ema_9 < ema_21 < ema_50:
        return "Bearish trend"
    if last_close > ema_21 and ema_9 > ema_21:
        return "Positive momentum"
    if last_close < ema_21 and ema_9 < ema_21:
        return "Negative momentum"
    return "Range / uncertain"


def analyze_market(df: pd.DataFrame, market_symbol: str = "BTC-USD", timeframe: str = "15m") -> dict[str, Any]:
    if df.empty:
        raise ValueError("Market data is empty; cannot analyze the instrument.")

    if len(df) < 20:
        raise ValueError("Not enough candles are available for analysis.")

    enriched = compute_indicators(df)
    last = enriched.iloc[-1]
    previous = enriched.iloc[-2]
    support_resistance = calculate_support_resistance(enriched)
    summary = candle_summary(enriched)
    pattern = detect_pattern(last)

    bullish_score = 0
    bearish_score = 0
    reasons: list[str] = []

    if last["close"] > last["ema_9"]:
        bullish_score += 1
        reasons.append("Close is above EMA 9.")
    else:
        bearish_score += 1
        reasons.append("Close is below EMA 9.")

    if last["ema_9"] > last["ema_21"]:
        bullish_score += 1
        reasons.append("EMA 9 is above EMA 21.")
    else:
        bearish_score += 1
        reasons.append("EMA 9 is below EMA 21.")

    if last["ema_21"] > last["ema_50"]:
        bullish_score += 1
        reasons.append("EMA 21 is above EMA 50.")
    else:
        bearish_score += 1
        reasons.append("EMA 21 is below EMA 50.")

    if last["rsi_14"] >= 55:
        bullish_score += 1
        reasons.append("RSI 14 is bullish.")
    elif last["rsi_14"] <= 45:
        bearish_score += 1
        reasons.append("RSI 14 is bearish.")
    else:
        reasons.append("RSI 14 is neutral.")

    if last["macd_hist"] > 0:
        bullish_score += 1
        reasons.append("MACD histogram is positive.")
    elif last["macd_hist"] < 0:
        bearish_score += 1
        reasons.append("MACD histogram is negative.")
    else:
        reasons.append("MACD histogram is flat.")

    if last["close"] > support_resistance["support"]:
        bullish_score += 1
        reasons.append("Price is holding above support.")
    else:
        bearish_score += 1
        reasons.append("Price is below support.")

    if last["high"] >= support_resistance["resistance"]:
        bullish_score += 1
        reasons.append("Price is approaching resistance.")
    else:
        bearish_score += 1
        reasons.append("Price remains below resistance.")

    if abs(last["close"] - previous["close"]) > 0 and last["close"] > previous["close"]:
        bullish_score += 1
        reasons.append("Recent close is stronger than the prior candle.")
    elif abs(last["close"] - previous["close"]) > 0:
        bearish_score += 1
        reasons.append("Recent close is weaker than the prior candle.")

    if last["atr_14"] > 0 and abs(last["close"] - last["ema_9"]) / last["atr_14"] < 1.2:
        reasons.append("Volatility is moderate to normal.")
    else:
        reasons.append("Volatility may be elevated or data is less certain.")

    if bullish_score > bearish_score and bullish_score >= 5:
        signal = "BUY"
    elif bearish_score > bullish_score and bearish_score >= 5:
        signal = "SELL"
    else:
        signal = "WAIT"

    trend = determine_trend(last["close"], last["ema_9"], last["ema_21"], last["ema_50"])
    invalidation_conditions = [
        "Signal invalidates if EMA 9 falls below EMA 21 while price remains below short-term support.",
        "Signal invalidates if RSI 14 crosses sharply into the opposite region without confirming volume expansion.",
        "Signal invalidates if volatility expands sharply beyond normal ATR conditions.",
        "Research signal is educational only and not an order to execute any position.",
    ]

    analysis = {
        "market_symbol": market_symbol,
        "timeframe": timeframe,
        "trend": trend,
        "possible_bullish_direction": "Bullish continuation is only considered if price remains above the EMA 9 and volume remains constructive.",
        "possible_bearish_direction": "Bearish continuation is only considered if price stays below EMA 9 and the MACD histogram remains negative.",
        "signal": signal,
        "reasons": reasons,
        "support": round(float(support_resistance["support"]), 4),
        "resistance": round(float(support_resistance["resistance"]), 4),
        "risk_level": "medium" if signal == "BUY" else "high" if signal == "SELL" else "low",
        "forecast_horizon": "Educational trend review across the next few candles; no guaranteed directional prediction is implied.",
        "analysis_timestamp": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "indicator_snapshot": {
            "ema_9": round(float(last["ema_9"]), 4),
            "ema_21": round(float(last["ema_21"]), 4),
            "ema_50": round(float(last["ema_50"]), 4),
            "rsi_14": round(float(last["rsi_14"]), 2),
            "macd_hist": round(float(last["macd_hist"]), 4),
            "atr_14": round(float(last["atr_14"]), 4),
            "pattern": pattern,
        },
        "candle_summary": summary,
        "invalidation_conditions": invalidation_conditions,
        "educational_only": True,
    }
    return analysis


__all__ = ["analyze_market", "determine_trend"]

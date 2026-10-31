from __future__ import annotations

import math
from typing import Any

import httpx
import pandas as pd

from app.config import settings

SUPPORTED_TIMEFRAMES = {
    "1m": "1min",
    "2m": "2min",
    "3m": "3min",
    "5m": "5min",
    "15m": "15min",
}

MARKETS = [
    {
        "symbol": "BTC-USD",
        "name": "Bitcoin / USD",
        "market_type": "cryptocurrency",
        "provider": "coingecko",
        "market_id": "bitcoin",
        "currency": "usd",
    },
    {
        "symbol": "ETH-USD",
        "name": "Ethereum / USD",
        "market_type": "cryptocurrency",
        "provider": "coingecko",
        "market_id": "ethereum",
        "currency": "usd",
    },
    {
        "symbol": "EUR-USD",
        "name": "Euro / US Dollar",
        "market_type": "forex",
        "provider": "manual",
        "market_id": None,
        "currency": "usd",
    },
    {
        "symbol": "XAU-USD",
        "name": "Gold / US Dollar",
        "market_type": "commodity",
        "provider": "manual",
        "market_id": None,
        "currency": "usd",
    },
]


def list_markets() -> list[dict[str, Any]]:
    return [
        {
            "symbol": market["symbol"],
            "name": market["name"],
            "market_type": market["market_type"],
            "provider": market["provider"],
            "available": market["market_id"] is not None or market["provider"] == "manual",
            "timeframes": list(SUPPORTED_TIMEFRAMES.keys()),
        }
        for market in MARKETS
    ]


def validate_market(symbol: str) -> dict[str, Any]:
    match = next((market for market in MARKETS if market["symbol"].lower() == symbol.lower()), None)
    if match is None:
        raise ValueError(f"Unsupported market: {symbol}")
    return match


def _normalize_intraday_candles(raw: list[list[float]]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(raw, columns=["timestamp_ms", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    df = df[["timestamp", "open", "high", "low", "close"]].copy()
    df["volume"] = 0.0
    return df


def _aggregate_dataframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.sort_values("timestamp").copy()
    time_rule = SUPPORTED_TIMEFRAMES.get(timeframe, "15min")
    grouped = df.resample(rule=time_rule, on="timestamp").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )
    grouped = grouped.reset_index().rename(columns={"timestamp": "timestamp"})
    return grouped


async def fetch_market_candles(symbol: str, timeframe: str = "15m", limit: int = 200) -> pd.DataFrame:
    market = validate_market(symbol)
    if market["provider"] != "coingecko" or not market["market_id"]:
        raise ValueError(f"Market {symbol} is unavailable from the configured public provider.")

    endpoint = f"{settings.coingecko_base_url}/coins/{market['market_id']}/ohlc"
    params = {"vs_currency": market["currency"], "days": "2"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:  # pragma: no cover - network path is tested indirectly
        raise ValueError(f"Unable to fetch candles for {symbol}: {exc}") from exc

    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected candle payload for {symbol}")

    df = _normalize_intraday_candles(payload)
    if df.empty:
        raise ValueError(f"No candle data available for market {symbol}.")

    df = _aggregate_dataframe(df, timeframe)
    if df.empty:
        raise ValueError(f"No aggregated candle data available for market {symbol} at timeframe {timeframe}.")

    df = df.tail(limit)
    df["market_symbol"] = symbol
    return df


def fetch_market_summary(symbol: str) -> dict[str, Any]:
    market = validate_market(symbol)
    return {
        "symbol": market["symbol"],
        "name": market["name"],
        "market_type": market["market_type"],
        "provider": market["provider"],
        "available": market["market_id"] is not None,
    }


__all__ = [
    "MARKETS",
    "SUPPORTED_TIMEFRAMES",
    "list_markets",
    "validate_market",
    "fetch_market_candles",
    "fetch_market_summary",
]

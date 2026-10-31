from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analysis import analyze_market
from app.backtesting import run_backtest
from app.config import settings
from app.market_data import fetch_market_candles, list_markets, validate_market
from app.paper_trading import DemoPaperTrading

rate_limit_store: dict[str, list[float]] = defaultdict(list)

app = FastAPI(title="RK AI Trading Analyzer", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = [ts for ts in rate_limit_store[ip] if now - ts < 60]
    if len(timestamps) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please slow down the request frequency."})
    timestamps.append(now)
    rate_limit_store[ip] = timestamps
    return await call_next(request)


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "provider": settings.data_provider,
        "timestamp": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.get("/api/markets")
async def markets() -> dict[str, Any]:
    return {"markets": list_markets(), "count": len(list_markets())}


@app.get("/api/candles")
async def candles(
    market: str = Query(default=settings.default_market, description="Market symbol such as BTC-USD"),
    timeframe: str = Query(default=settings.default_timeframe, description="Timeframe like 15m"),
    limit: int = Query(default=200, ge=20, le=500),
):
    try:
        validate_market(market)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        df = await fetch_market_candles(market, timeframe=timeframe, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "market": market,
        "timeframe": timeframe,
        "count": len(df),
        "candles": [
            {
                "timestamp": row["timestamp"].isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for _, row in df.iterrows()
        ],
    }


@app.get("/api/analyze")
async def analyze(
    market: str = Query(default=settings.default_market),
    timeframe: str = Query(default=settings.default_timeframe),
    limit: int = Query(default=200, ge=20, le=500),
):
    try:
        validate_market(market)
        df = await fetch_market_candles(market, timeframe=timeframe, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = analyze_market(df, market_symbol=market, timeframe=timeframe)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result


@app.get("/api/indicators")
async def indicators(
    market: str = Query(default=settings.default_market),
    timeframe: str = Query(default=settings.default_timeframe),
    limit: int = Query(default=200, ge=20, le=500),
):
    try:
        validate_market(market)
        df = await fetch_market_candles(market, timeframe=timeframe, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    last = df.iloc[-1]
    return {
        "market": market,
        "timeframe": timeframe,
        "timestamp": last["timestamp"].isoformat(),
        "close": float(last["close"]),
        "open": float(last["open"]),
        "high": float(last["high"]),
        "low": float(last["low"]),
        "volume": float(last["volume"]),
        "ema_9": float(last["close"]),
        "ema_21": float(last["close"]),
        "ema_50": float(last["close"]),
    }


@app.get("/api/history")
async def history(limit: int = Query(default=10, ge=1, le=50)) -> dict[str, Any]:
    return {"history": [], "count": 0, "limit": limit, "demo": True}


@app.post("/api/backtest")
async def backtest(request: dict[str, Any]):
    market = request.get("market", settings.default_market)
    timeframe = request.get("timeframe", settings.default_timeframe)
    initial_balance = request.get("initial_balance", 10000.0)
    spread = request.get("spread", 0.0008)
    slippage = request.get("slippage", 0.0005)

    try:
        validate_market(market)
        df = await fetch_market_candles(market, timeframe=timeframe, limit=200)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        results = run_backtest(
            df,
            initial_balance=float(initial_balance),
            spread=float(spread),
            slippage=float(slippage),
            market_symbol=market,
            timeframe=timeframe,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return results


@app.get("/")
async def landing() -> dict[str, str]:
    return {"message": "RK AI Trading Analyzer backend is running."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)

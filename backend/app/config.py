from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_markets_endpoint():
    response = client.get("/api/markets")
    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_analyze_endpoint_invalid_market():
    response = client.get("/api/analyze?market=INVALID")
    assert response.status_code == 400


def test_backtest_endpoint_invalid_market():
    response = client.post("/api/backtest", json={"market": "INVALID"})
    assert response.status_code == 400

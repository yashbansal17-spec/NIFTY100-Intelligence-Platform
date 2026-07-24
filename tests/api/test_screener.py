from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_screener_min_roe_filter():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    for row in response.json():
        assert row["return_on_equity_pct"] is None or row["return_on_equity_pct"] >= 15


def test_screener_invalid_parameter_returns_400():
    response = client.get("/api/v1/screener?min_roe=999999999")
    assert response.status_code == 400

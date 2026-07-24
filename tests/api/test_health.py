from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "companies" in data["db_row_counts"]

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_sectors_returns_expected_count():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    assert len(response.json()) >= 10


def test_sector_companies_filter():
    response = client.get("/api/v1/sectors/IT/companies")
    assert response.status_code in {200, 404}
    if response.status_code == 200:
        assert all("IT" in row["broad_sector"] or row["broad_sector"] == "Information Technology" for row in response.json())

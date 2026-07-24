from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_companies_returns_records():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    assert len(response.json()) >= 90


def test_tcs_profile_or_dataset_compatible():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code in {200, 404}
    if response.status_code == 200:
        assert response.json()["id"] == "TCS"


def test_invalid_company_404():
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404

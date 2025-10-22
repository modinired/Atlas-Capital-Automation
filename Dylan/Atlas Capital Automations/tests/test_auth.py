from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_api_key_required() -> None:
    """When API_KEY is set, requests without the header should fail with 401."""
    # Set a temporary API key and create a client
    original_key = settings.api_key
    settings.api_key = "test-secret"
    client = TestClient(app)
    payload = {
        "debt_to_income": 0.4,
        "credit_utilization": 0.3,
        "age_years": 42,
        "savings_ratio": 0.2,
        "has_delinquency": 0,
    }
    # Without header
    r = client.post("/v1/risk/score", json=payload)
    assert r.status_code == 401
    # With wrong key
    r = client.post("/v1/risk/score", json=payload, headers={"X-API-Key": "wrong"})
    assert r.status_code == 401
    # With correct key
    r = client.post("/v1/risk/score", json=payload, headers={"X-API-Key": "test-secret"})
    assert r.status_code == 200
    # Restore original
    settings.api_key = original_key
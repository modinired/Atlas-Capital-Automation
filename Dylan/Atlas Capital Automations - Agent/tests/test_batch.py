from fastapi.testclient import TestClient
from app.main import app


def test_batch_scoring_returns_list_of_results() -> None:
    """Ensure the batch endpoint returns a list of scoring results matching input size."""
    client = TestClient(app)
    payloads = [
        {
            "debt_to_income": 0.4,
            "credit_utilization": 0.3,
            "age_years": 42,
            "savings_ratio": 0.2,
            "has_delinquency": 0,
        },
        {
            "debt_to_income": 1.0,
            "credit_utilization": 0.5,
            "age_years": 35,
            "savings_ratio": 0.1,
            "has_delinquency": 1,
        },
    ]
    r = client.post("/v1/risk/score/batch", json=payloads)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == len(payloads)
    # Each element should contain expected keys
    for item in data:
        assert "probability" in item and "label" in item and "audit" in item
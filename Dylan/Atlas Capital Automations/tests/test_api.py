from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.text == "ok"

def test_risk_score_valid():
    payload = {
        "debt_to_income": 0.4,
        "credit_utilization": 0.3,
        "age_years": 42,
        "savings_ratio": 0.2,
        "has_delinquency": 0
    }
    r = client.post("/v1/risk/score", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "probability" in data and "label" in data and "audit" in data
    assert abs(data["probability"] - float(data["probability"])) < 1e-9

def test_risk_score_validation():
    bad_payload = {
        "debt_to_income": -1,
        "credit_utilization": 2,
        "age_years": 10,
        "savings_ratio": -0.1,
        "has_delinquency": 3
    }
    r = client.post("/v1/risk/score", json=bad_payload)
    assert r.status_code == 422

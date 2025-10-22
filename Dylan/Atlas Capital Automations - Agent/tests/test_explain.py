import math
from fastapi.testclient import TestClient
from app.main import app


def test_explain_endpoint_linear_contributions() -> None:
    """Verify that the explain endpoint returns correct contributions and probability.

    The built‑in model uses fixed weights and bias.  For a known input the
    endpoint should return contributions equal to weight × value and compute
    the linear score and probability accordingly.  We do not test the exact
    probability against a fixed value, but we verify that it matches the
    logistic of the linear score.
    """
    client = TestClient(app)
    payload = {
        "debt_to_income": 0.5,
        "credit_utilization": 0.2,
        "age_years": 30,
        "savings_ratio": 0.3,
        "has_delinquency": 1,
    }
    r = client.post("/v1/risk/explain", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    contributions = data["contributions"]
    # Compute expected contributions manually using built‑in weights
    expected = {
        "debt_to_income": 2.1 * payload["debt_to_income"],
        "credit_utilization": 1.3 * payload["credit_utilization"],
        "age_years": -0.02 * payload["age_years"],
        "savings_ratio": -1.1 * payload["savings_ratio"],
        "has_delinquency": 1.8 * payload["has_delinquency"],
    }
    # Check each contribution within a small tolerance
    for k, v in expected.items():
        assert math.isclose(contributions[k], v, rel_tol=1e-9, abs_tol=1e-9)
    # Verify the linear score equals intercept + sum(contributions)
    linear_score = data["linear_score"]
    intercept = data["intercept"]
    assert math.isclose(
        linear_score,
        intercept + sum(expected.values()),
        rel_tol=1e-9,
        abs_tol=1e-9,
    )
    # Verify probability is sigmoid(linear_score)
    prob = data["probability"]
    # compute logistic function with protection for extremes
    def sigmoid(z: float) -> float:
        return 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))
    assert math.isclose(prob, sigmoid(linear_score), rel_tol=1e-9, abs_tol=1e-9)
import importlib
import os

from fastapi.testclient import TestClient


def test_rate_limiting_enforced() -> None:
    """Verify that exceeding the configured rate limit returns a 429 error."""
    # Set rate limit to 2 requests per minute
    prev = os.environ.get("RATE_LIMIT_PER_MIN")
    os.environ["RATE_LIMIT_PER_MIN"] = "2"
    # Reload the rate_limiter module to pick up the new env var
    import app.rate_limiter as rl  # type: ignore
    importlib.reload(rl)
    # Also reload the main app to ensure the middleware uses the new limiter
    import app.main as main_module  # type: ignore
    importlib.reload(main_module)
    client = TestClient(main_module.app)
    payload = {
        "debt_to_income": 0.4,
        "credit_utilization": 0.3,
        "age_years": 42,
        "savings_ratio": 0.2,
        "has_delinquency": 0,
    }
    # First two requests succeed
    assert client.post("/v1/risk/score", json=payload).status_code == 200
    assert client.post("/v1/risk/score", json=payload).status_code == 200
    # Third request should be rate limited
    r = client.post("/v1/risk/score", json=payload)
    assert r.status_code == 429
    # Clean up: restore environment and reload modules back to default settings
    if prev is None:
        del os.environ["RATE_LIMIT_PER_MIN"]
    else:
        os.environ["RATE_LIMIT_PER_MIN"] = prev
    importlib.reload(rl)
    importlib.reload(main_module)
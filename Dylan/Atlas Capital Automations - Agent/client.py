"""
Python client for Terry Delmonaco Presents: AI API.

This module provides convenience functions for interacting with the REST API
exposed by the service.  It uses the requests library to perform HTTP calls.

Example usage:

    from client import Client

    client = Client(base_url="http://localhost:8000", api_key="my-secret-key")
    result = client.score({
        "debt_to_income": 0.5,
        "credit_utilization": 0.3,
        "age_years": 40,
        "savings_ratio": 0.2,
        "has_delinquency": 0,
    })
    print(result.probability, result.label)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests


@dataclass
class ScoreResult:
    probability: float
    label: int
    model_version: str
    audit: Dict[str, float]


@dataclass
class ExplainResult:
    contributions: Dict[str, float]
    intercept: float
    linear_score: float
    probability: float


class Client:
    def __init__(self, base_url: str, api_key: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def health(self) -> str:
        r = requests.get(f"{self.base_url}/health")
        r.raise_for_status()
        return r.text

    def score(self, payload: Dict[str, Any]) -> ScoreResult:
        r = requests.post(
            f"{self.base_url}/v1/risk/score",
            headers=self._headers(),
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        return ScoreResult(**data)

    def score_batch(self, payloads: List[Dict[str, Any]]) -> List[ScoreResult]:
        r = requests.post(
            f"{self.base_url}/v1/risk/score/batch",
            headers=self._headers(),
            json=payloads,
        )
        r.raise_for_status()
        data = r.json()
        return [ScoreResult(**item) for item in data]

    def explain(self, payload: Dict[str, Any]) -> ExplainResult:
        r = requests.post(
            f"{self.base_url}/v1/risk/explain",
            headers=self._headers(),
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        return ExplainResult(**data)
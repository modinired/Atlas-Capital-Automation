from dataclasses import dataclass
from typing import Dict, Optional, List
import os
import pickle

from app.config import settings

@dataclass
class RiskModel:
    # Simple logistic regression with fixed coefficients for deterministic output.
    bias: float = -1.25
    weights: Dict[str, float] = None

    #: Optional external model loaded from a pickle file. If provided via the
    #: MODEL_PATH environment variable, it will be used instead of the fixed
    #: coefficients. The external model must implement a `predict_proba` method that
    #: accepts a 2D list/array of feature values and returns probabilities for the
    #: positive class in the second column.
    external_model: Optional[object] = None

    def __post_init__(self):
        if self.weights is None:
            self.weights = {
                "debt_to_income": 2.1,
                "credit_utilization": 1.3,
                "age_years": -0.02,
                "savings_ratio": -1.1,
                "has_delinquency": 1.8,
            }
        # Attempt to load an external model if a path is provided and the file exists.
        model_path = settings.model_path
        if model_path and os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    loaded = pickle.load(f)
                # Expect the loaded object to have a predict_proba method.
                if hasattr(loaded, "predict_proba"):
                    self.external_model = loaded
            except Exception:
                # Fall back silently to built‑in coefficients if loading fails.
                self.external_model = None

    @staticmethod
    def _sigmoid(x: float) -> float:
        import math
        if x >= 0:
            z = math.exp(-x)
            return 1.0 / (1.0 + z)
        else:
            z = math.exp(x)
            return z / (1.0 + z)

    def predict_proba(self, features: Dict[str, float]) -> float:
        # If an external model is provided, use it for probability estimation.
        if self.external_model is not None:
            # Ensure the feature vector is ordered consistently with the training data.
            ordered: List[float] = [
                float(features.get(k, 0.0)) for k in self.weights.keys()
            ]
            try:
                proba = self.external_model.predict_proba([ordered])[0][1]
                return float(proba)
            except Exception:
                # If external model call fails, fall back to built‑in implementation.
                pass
        # Built‑in logistic regression with fixed coefficients.
        score = self.bias
        for k, w in self.weights.items():
            v = float(features.get(k, 0.0))
            score += w * v
        return self._sigmoid(score)

    def predict_label(self, features: Dict[str, float], threshold: float = 0.5) -> int:
        return int(self.predict_proba(features) >= threshold)

model = RiskModel()

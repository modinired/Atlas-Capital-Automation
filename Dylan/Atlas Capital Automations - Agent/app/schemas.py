from pydantic import BaseModel, Field, conint, confloat
from typing import Dict

class RiskInput(BaseModel):
    debt_to_income: confloat(ge=0, le=5) = Field(..., description="Debt-to-income ratio, 0..5")
    credit_utilization: confloat(ge=0, le=1) = Field(..., description="Credit utilization 0..1")
    age_years: conint(ge=18, le=100) = Field(..., description="Age in years")
    savings_ratio: confloat(ge=0, le=5) = Field(..., description="Savings/income ratio, 0..5")
    has_delinquency: conint(ge=0, le=1) = Field(..., description="1 if any delinquency in last 24 months")

    # Forbid unknown fields and enable strict validation
    model_config = {
        "extra": "forbid",
    }

class RiskOutput(BaseModel):
    probability: float
    label: int
    model_version: str
    audit: Dict[str, float]


class ExplainOutput(BaseModel):
    """Response model for the risk explanation endpoint.

    Attributes:
        contributions: Per-feature contribution to the linear score (weight × value).
        intercept: The intercept term (bias) of the logistic regression model.
        linear_score: The sum of contributions plus intercept.
        probability: The probability obtained by applying the sigmoid to the linear score.
    """

    contributions: Dict[str, float]
    intercept: float
    linear_score: float
    probability: float

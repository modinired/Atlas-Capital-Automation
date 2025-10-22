from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from time import time
from typing import Dict, List

from app.config import settings
from app.schemas import RiskInput, RiskOutput
from app.model import model
from app.logging_utils import configure_logging
from app.security import get_api_key
from app.rate_limiter import enforce_rate_limit
from app.schemas import ExplainOutput
from app import db
from app.telemetry import init_tracing
from fastapi import WebSocket

logger = configure_logging(settings.log_level)

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["endpoint"])

app = FastAPI(title=settings.service_name, version=settings.service_version)

# -----------------------------------------------------------------------------
# CORS configuration
#
# Allow the dashboard (running on a separate port) to call this API.  Adjust
# allowed origins for your deployment.  We allow localhost on typical Vite
# ports for development purposes.
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Application lifecycle hooks
# -----------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize application resources."""
    # Create database tables at startup.
    db.create_tables()
    # Initialize distributed tracing if enabled.  This must be done after
    # the app is created but before requests are processed.
    try:
        init_tracing(app)
    except Exception:
        # Tracing is optional; if initialization fails, log and continue.
        logger.exception("tracing_init_error")

@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    """Enforce the per‑identifier rate limit before processing the request."""
    await enforce_rate_limit(request)
    return await call_next(request)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Collect Prometheus metrics for each request."""
    start = time()
    response = await call_next(request)
    latency = time() - start
    endpoint = request.url.path
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=str(response.status_code)).inc()
    return response

@app.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "ok"

@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return PlainTextResponse(content=data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

@app.post("/v1/risk/score", response_model=RiskOutput)
async def risk_score(
    payload: RiskInput,
    api_key: str = Depends(get_api_key),
) -> RiskOutput:
    try:
        features: Dict[str, float] = payload.model_dump()
        proba = model.predict_proba(features)
        label = model.predict_label(features, threshold=0.5)
        logger.info("risk_scored", extra={"features": features, "probability": proba, "label": label})
        # Persist the request and result to the database asynchronously.  The api_key
        # may be empty if authentication is disabled.
        try:
            await db.log_request_async(features, proba, label, api_key)
        except Exception:
            logger.exception("db_log_error")
        return RiskOutput(
            probability=round(proba, 6),
            label=label,
            model_version="1.0.0",
            audit=features,
        )
    except Exception as e:
        logger.exception("risk_score_error")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/risk/explain", response_model=ExplainOutput)
async def risk_explain(
    payload: RiskInput,
    api_key: str = Depends(get_api_key),
) -> ExplainOutput:
    """Explain the linear contributions of each feature to the risk score.

    This endpoint computes the product of each feature value and its corresponding
    weight in the logistic regression model, adds the intercept (bias), and
    returns the linear score and probability.  If an external model is
    configured, the contributions are still computed from the built‑in weights,
    but the probability is calculated using the linear score via the sigmoid
    function.  For a full explanation of externally trained models, use model-
    specific explainability techniques (e.g. SHAP).
    """
    features: Dict[str, float] = payload.model_dump()
    # Compute per-feature contributions using built‑in weights
    contributions: Dict[str, float] = {}
    for name, weight in model.weights.items():
        val = float(features.get(name, 0.0))
        contributions[name] = weight * val
    linear_score = model.bias + sum(contributions.values())
    probability = model._sigmoid(linear_score)
    return ExplainOutput(
        contributions=contributions,
        intercept=model.bias,
        linear_score=linear_score,
        probability=probability,
    )


@app.post("/v1/risk/score/batch", response_model=List[RiskOutput])
async def risk_score_batch(
    payloads: List[RiskInput],
    api_key: str = Depends(get_api_key),
) -> List[RiskOutput]:
    """Score multiple payloads in a single request.

    This endpoint accepts a list of `RiskInput` objects and returns a list of
    corresponding `RiskOutput` results.  Each request is logged individually.
    """
    results: List[RiskOutput] = []
    for payload in payloads:
        features: Dict[str, float] = payload.model_dump()
        proba = model.predict_proba(features)
        label = model.predict_label(features)
        logger.info(
            "risk_scored_batch",
            extra={"features": features, "probability": proba, "label": label, "batch": True},
        )
        try:
            await db.log_request_async(features, proba, label, api_key)
        except Exception:
            logger.exception("db_log_error")
        results.append(
            RiskOutput(
                probability=round(proba, 6),
                label=label,
                model_version="1.0.0",
                audit=features,
            )
        )
    return results


# -----------------------------------------------------------------------------
# WebSocket streaming endpoint
# -----------------------------------------------------------------------------

@app.websocket("/ws/risk")
async def risk_score_websocket(websocket: WebSocket) -> None:
    """Accept risk scoring requests over a WebSocket.

    Clients connect to this endpoint and send JSON objects representing the
    input features (matching the ``RiskInput`` schema).  The server responds
    with JSON containing the predicted probability, label and audit fields.  If
    API key authentication is enabled, clients must supply the key as a
    query parameter named ``api_key`` when opening the connection.  Connections
    with invalid keys are closed immediately.
    """
    # Check API key as a query parameter if authentication is enabled.
    expected_key = settings.api_key
    if expected_key:
        provided_key = websocket.query_params.get("api_key")
        if provided_key != expected_key:
            # Close with policy violation code (1008)
            await websocket.close(code=1008, reason="Invalid or missing API key")
            return
    await websocket.accept()
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except Exception:
                # Invalid JSON or connection closed by client
                break
            # Validate and compute probability using the same logic as the REST API.
            try:
                features: Dict[str, float] = RiskInput(**data).model_dump()
            except Exception as exc:
                await websocket.send_json({"error": f"Invalid input: {exc}"})
                continue
            proba = model.predict_proba(features)
            label = model.predict_label(features)
            # Log asynchronously
            try:
                await db.log_request_async(features, proba, label, expected_key or "")
            except Exception:
                logger.exception("db_log_error")
            await websocket.send_json({
                "probability": round(proba, 6),
                "label": label,
                "audit": features,
            })
    except Exception:
        # Log unexpected server errors
        logger.exception("websocket_error")
    finally:
        await websocket.close()

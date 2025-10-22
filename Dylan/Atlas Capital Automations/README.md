# Terry Delmonaco Presents: AI

This codebase brings together the best pieces of the original Atlas Capital service with the "Agent Atlas Capital Automation" project.  
It is a production‑ready FastAPI service with CI/CD templates, Docker packaging, Kubernetes manifests, tests and observability wired in.  
The core application implements a deterministic risk scoring endpoint, but the modular structure makes it easy to extend or replace with your own logic.

## Authentication & Configuration

This service secures the `/v1/risk/score` endpoint with a simple API key.  Clients must
provide the key in the `X-API-Key` HTTP header.  Set the `API_KEY` environment
variable before starting the server to enable authentication.  When `API_KEY` is
unset, authentication is disabled.

You can also load a trained risk model from a pickle file by setting the
`MODEL_PATH` environment variable to the path of a serialized scikit‑learn model.
If no path is provided, the service falls back to a built‑in logistic regression
with fixed coefficients.  For production scenarios, train a model on
representative data and mount the resulting file at runtime.

## Quickstart

```bash
# 1) Run locally (dev)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2) Docker
# Build the Docker image for the new service
docker build -t terry-delmonaco-presents-ai:1.0.0 .
# Run it with production environment variables
docker run -p 8000:8000 --env ENV=prod --env LOG_LEVEL=INFO terry-delmonaco-presents-ai:1.0.0

# 3) Tests
pytest -q

# 4) Kubernetes (example, requires a cluster and `kubectl` context)
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
# Optional ingress if you have an ingress controller installed:
kubectl apply -f k8s/ingress.yaml
```

### Quick launch scripts

In addition to running the API via Uvicorn or Docker, this repository provides a **quick‑launch** mechanism for end users who prefer a double‑click experience.  The following files are included in the project root:

- **`scripts/launch.py`** – a Python helper that starts both the risk scoring API and the MCP server on configurable ports and opens your default web browser to the interactive docs.  It honours all environment variables (`API_KEY`, `RATE_LIMIT_PER_MIN`, `MODEL_PATH`, etc.) and uses Uvicorn to serve the applications.  Run it from an activated virtual environment:

  ```bash
  python scripts/launch.py
  ```

- **`launch.sh`** – a shell script for Linux users.  It activates the virtual environment if it exists and invokes the Python launcher.  Make it executable (`chmod +x launch.sh`) and double‑click it in your file manager or run `./launch.sh` from a terminal.

- **`launch.command`** – a macOS‑friendly wrapper (identical to `launch.sh`) that Finder will recognise as an executable.  Double‑clicking it opens Terminal and runs the launcher.

- **`launch.bat`** – a batch script for Windows.  It activates the virtual environment and runs `python scripts\launch.py`.  Double‑click the file in Explorer to start the services.  You can create a shortcut to this batch file and assign a custom icon in its properties to create a polished desktop launcher.

These scripts provide a convenient way to start the API and MCP together without remembering the Uvicorn commands.  For production deployments, continue using Docker or Kubernetes as described above.

Endpoints:

- `GET /health` — health probe
- `GET /metrics` — Prometheus metrics
- `POST /v1/risk/score` — risk score with audited inputs
- `POST /v1/risk/explain` — returns per‑feature contributions, linear score and probability
- `POST /v1/risk/score/batch` — score a list of inputs in one request
- `POST /mcp/codeexec/execute` — execute a code snippet in a sandboxed
  subprocess via the new CodeExec MCP.  Accepts JSON with
  ``code`` and optional ``language``, ``args`` and ``timeout`` fields.
- **WebSocket:** `ws://<host>/ws/risk` — send JSON payloads over a persistent connection and receive streaming scores.  When authentication is enabled, pass the API key as a query parameter (e.g., `ws://host/ws/risk?api_key=YOUR_KEY`).

## Rate limiting

Set the `RATE_LIMIT_PER_MIN` environment variable to a positive integer to
enable per‑API‑key/IP rate limiting.  The service will reject requests with a
429 response when more than the specified number of requests are received
within a rolling one‑minute window.

For production‑grade rate limiting across multiple instances, deploy an API
gateway or use a shared backend such as Redis.  The built‑in implementation
operates in process memory and is meant for single‑instance or demonstration
use only.

## Distributed tracing

The service includes optional OpenTelemetry tracing.  To enable it, set
`ENABLE_TRACES=true` and provide an OTLP collector endpoint via `OTLP_ENDPOINT`.
At startup the application will configure a tracer provider, export spans to
the collector and automatically instrument FastAPI.  This allows you to view
end‑to‑end traces of incoming requests in your observability platform.

Example:

```bash
OTLP_ENDPOINT=http://otel-collector:4318 ENABLE_TRACES=true uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Autoscaling with Kubernetes

An example Horizontal Pod Autoscaler manifest (`k8s/hpa.yaml`) scales the API
deployment based on CPU utilization.  Apply this file in addition to the
deployment and service to automatically scale between 2 and 10 replicas when
the observed CPU load exceeds 70%.

```bash
kubectl apply -f k8s/hpa.yaml
```

Modify the `minReplicas`, `maxReplicas` and `averageUtilization` values to
suit your workload and cluster capacity.

## Training a model

Use the provided `scripts/train_model.py` to train a logistic regression
model on your own CSV dataset.  The script uses pure Python to perform
batch gradient descent and saves the resulting model as a pickle file that can
be loaded via the `MODEL_PATH` environment variable.

Example:

```bash
python scripts/train_model.py --data credit_training.csv --output model.pkl --epochs 2000 --lr 0.01
# Then start the API with MODEL_PATH=model.pkl
MODEL_PATH=model.pkl uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Fairness evaluation

To assess demographic parity of your model, run `scripts/evaluate_fairness.py` on
a labeled dataset containing a `sensitive` column.  The script reports the
average predicted probability per group and the absolute difference between
groups.

Example:

```bash
python scripts/evaluate_fairness.py --data credit_test.csv --model model.pkl
```

## Python client

The project includes a simple Python client (`client.py`) that wraps the API
endpoints.  Use it in your applications to integrate scoring and explanation
functionality.

Security & quality:
- Pre-commit with `black`, `isort`, `flake8`, `bandit`
- CI checks via GitHub Actions
- Minimal dependency set

## Symbiotic Recursive Cognition (SRC) & MCP Integration

In addition to the core risk scoring API, this codebase now includes a
prototype implementation of the CESAR‑SRC **Symbiotic Recursive
Cognition** architecture using a **Multi‑Component Platform (MCP)**
design.  The MCP modules live under the `mcp/` package and provide
composable services for knowledge retrieval, model routing, policy
enforcement, workflow orchestration and telemetry.  They are designed
to be lightweight and extendable without replacing the underlying risk
scoring logic.

### Key MCP services

- **Knowledge MCP** (`mcp/knowledge.py`) – a small evidence store backed
  by SQLite.  It supports `ground()` to retrieve documents and
  `writeback()` to persist new information.  Documents are ranked by
  naive keyword overlap but the interface can be swapped for a vector
  database in production.
- **Triangulator MCP** (`mcp/triangulator.py`) – routes tasks across a
  pool of models (initially two local echo/reverse functions) and
  adjudicates their outputs based on a configurable rubric.  It also
  exposes a simple self‑check heuristic to score outputs for
  faithfulness, PII content and reasoning depth.
- **CodeExec MCP** (`mcp/codeexec.py`) – executes short code snippets in a
  sandboxed subprocess.  Inspired by Manus’ code‑execution engine, it
  currently supports Python and returns captured stdout, stderr,
  returncodes and timeout indicators.  This enables workflows to
  perform dynamic computations as part of a Card while still
  benefiting from policy enforcement and telemetry.  Future
  extensions could add interpreters for additional languages or
  containerised execution for stronger isolation.
- **Policy MCP** (`mcp/policy.py`) – enforces content policies and
  performs redaction using regular expressions.  The built‑in
  `no_pii` policy masks email addresses and social security numbers.
  Additional policies can be added easily.
- **Workflow MCP** (`mcp/workflow.py`) – executes task plans defined
  in declarative “Cards”.  It handles argument interpolation, gating
  on policy results and context management.  Cards are defined in
  `mcp/cards.py` with two examples: Quarterly Business Review (QBR)
  and Incident Postmortem.
- **Telemetry MCP** (`mcp/telemetry.py`) – wraps Prometheus counters
  and OpenTelemetry spans so MCP calls can emit metrics and traces
  consistently.

### Running the MCP server

The module `app/mcp_api.py` exposes the MCP services via HTTP
endpoints under the `/mcp` prefix using FastAPI.  To start the MCP
server on port 9000, activate your virtual environment and run:

```bash
uvicorn app.mcp_api:mcp_app --host 0.0.0.0 --port 9000 --reload
```

You can then execute a Card by POSTing to `/mcp/cards/{card_name}`
with a JSON body containing the card inputs.  For example, to run
the QBR card:

```bash
curl -X POST http://localhost:9000/mcp/cards/QBR \
    -H 'Content-Type: application/json' \
    -d '{"accounts": ["ACME"], "time_window": "90d", "kpi_definitions": {}, "file_locations": {}}'
```

This will retrieve KPI evidence, generate candidate summaries via
the Triangulator, adjudicate them, enforce the no‑PII policy and
return a dossier with the judgement and evidence.  See
`mcp/cards.py` for details.

### Extending the MCP

The MCP architecture is intended to evolve without disturbing your
core logic.  You can add new models to the Triangulator by
registering async functions in `mcp/triangulator.MODEL_REGISTRY`.
Policies can be extended by adding new case branches in
`mcp/policy.enforce` and regular expressions in
`mcp/policy.redact`.  The knowledge store can be swapped for a
vector database by replacing the naive retrieval function in
`mcp/knowledge.ground`.

Cards provide a declarative way to encode high‑level processes.
By defining plans in `mcp/cards.py`, you can orchestrate complex
workflows across multiple MCP services and embed recursion, gates
and evidence contracts in a structured format.  The provided
examples demonstrate how to build Quarterly Business Review and
Incident Postmortem workflows.  Feel free to create your own
cards tailored to your business needs.

# Terry Delmonaco Presents: AI — Agent Edition

This repository is the **Agent Edition** of the Terry Delmonaco Presents: AI platform.  It includes everything from the standalone edition—risk scoring API, Multi‑Component Platform (MCP) modules and infrastructure—but adds a companion **Orchestrator Agent** that can run Card workflows end‑to‑end on your behalf.  Use this edition if you want a drop‑in “manager” agent that coordinates the Knowledge, Triangulator and Policy MCPs according to Card descriptors, such as Quarterly Business Review or Incident Postmortem.

The underlying services remain production‑ready FastAPI applications with CI/CD templates, Docker packaging, Kubernetes manifests, tests and observability.  The agent script uses the MCP primitives directly, so it does not require any external orchestration service.  See `scripts/agent_orchestrator.py` for details.

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

This edition includes the same quick‑launch helpers as the standalone version, allowing you to start both the API and MCP server with a single click.  The following files are included in the project root:

- **`scripts/launch.py`** – a Python launcher that starts the risk API and MCP server, waits briefly and opens your default browser to the Swagger documentation.  It respects all configuration environment variables and uses default ports 8000/9000.  Run it from your virtual environment:

  ```bash
  python scripts/launch.py
  ```

- **`launch.sh`** – a Linux shell wrapper that activates `.venv` and calls the Python launcher.  Make it executable (`chmod +x launch.sh`) and double‑click it in your file manager or run `./launch.sh`.

- **`launch.command`** – a macOS variant of the shell wrapper, recognised by Finder.  Double‑click to open Terminal and run the services.

- **`launch.bat`** – a Windows batch file that activates `.venv` and runs the Python launcher.  Double‑click it in Explorer to start everything.  You can create a shortcut to this file and assign a custom icon for a polished desktop experience.

These scripts provide a convenient alternative to the standard Uvicorn commands.  They start both the API and the MCP at once and open the docs automatically, while still honouring environment variables like `API_KEY` and `RATE_LIMIT_PER_MIN`.  For production deployments, continue using Docker or Kubernetes as detailed above.

Endpoints:

- `GET /health` — health probe
- `GET /metrics` — Prometheus metrics
- `POST /v1/risk/score` — risk score with audited inputs
- `POST /v1/risk/explain` — returns per‑feature contributions, linear score and probability
- `POST /v1/risk/score/batch` — score a list of inputs in one request
 - **WebSocket:** `ws://<host>/ws/risk` — send JSON payloads over a persistent connection and receive streaming scores.  When authentication is enabled, pass the API key as a query parameter (e.g., `ws://host/ws/risk?api_key=YOUR_KEY`).

 - `POST /mcp/codeexec/execute` — execute a code snippet in a sandboxed
   subprocess via the new CodeExec MCP.  Provide a JSON object with
   ``code`` (the source to run) and optional ``language`` (defaults to
   ``"python"``), ``args`` (list of command line arguments) and
   ``timeout`` (seconds).  The endpoint returns captured stdout,
   stderr, the process return code and a ``timed_out`` flag.

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
- **CodeExec MCP** (`mcp/codeexec.py`) – executes short code snippets
  in a sandboxed subprocess.  Inspired by Manus’ execution engine,
  it currently supports Python and returns stdout, stderr, return
  codes and timeout flags.  This enables cards to perform dynamic
  computations or run CLI‑style tasks as part of a workflow, while
  still integrating with policy enforcement and telemetry.  Future
  extensions could add support for other languages and stronger
  isolation via containers.
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

## Orchestrator Agent

The defining feature of the Agent Edition is the **Orchestrator Agent**
implemented in `scripts/agent_orchestrator.py`.  This command‑line
utility loads your chosen Card, executes its plan via the MCP
services and prints the resulting decision dossier.  It therefore
embodies the Symbiotic Recursive Cognition loop (Plan → Ground →
Propose → Critique → Repair → Policy‑Gate → Deliver) described in
the CESAR‑SRC architecture.  Running the orchestrator does not
require any additional services beyond the MCP and risk scoring API.

### Running a Card

To execute a Card end‑to‑end, prepare a JSON file containing the
required inputs.  For example, to run the Quarterly Business Review
(QBR) Card with inputs in `qbr_inputs.json`:

```bash
python scripts/agent_orchestrator.py --card QBR --inputs qbr_inputs.json
```

The script will load the Card definition, call the Knowledge, Triangulator
and Policy MCPs as specified in the plan, and output the final dossier
as prettified JSON to stdout.  See `mcp/cards.py` for the expected
input schema for each Card (e.g. account names, lookback windows).

### CLI Agent tools

In addition to high‑level Cards, the MCP also exposes low‑level
tools suitable for automating build and deployment tasks.  These
reside in `mcp/cli_agent.py` and wrap basic shell operations:

- **exec** – run a shell command with optional arguments and timeout,
  returning the captured stdout, stderr and exit code.  Use this to
  invoke local scripts or utilities.
- **edit_repo** – perform file operations (create, modify, delete)
  relative to a repository root.  This can be used by Cards to
  programmatically update configuration files.
- **test** – run pytest on a specified test suite and return the
  captured output.  Useful for continuous integration workflows.

These tools are not exposed via the REST API by default but can be
invoked directly from Python or used within new Cards to add custom
logic.  Be mindful that executing shell commands poses security
risks; sandboxing and access controls should be implemented in
production.

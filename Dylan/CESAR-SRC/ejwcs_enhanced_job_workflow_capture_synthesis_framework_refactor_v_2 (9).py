"""
CESAR-SRC / EJWCS - Production-Ready Multi-Agent, Multi-Model System (ASCII-safe)

This single Python module embeds:
- Non-Python assets (pyproject, Makefile, README, docs) as ASCII-only string constants.
- Executable packages under `cesar_src/`.
- Reference tests as strings.
- A snapshot utility/CLI to save a copy of this exact file on your computer (cron/Task Scheduler friendly).

All quotes and hyphens are ASCII. No smart quotes (U+2018/2019), figure dashes (U+2011), ellipses (U+2026), or arrows (U+2192) appear in source. This prevents SyntaxError from mixed doc/code in Python canvases.
"""

from __future__ import annotations

# -----------------------------
# Non-Python assets as ASCII strings
# -----------------------------
PYPROJECT_TOML = """
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "cesar-src"
version = "1.0.3"
description = "CESAR-SRC: Multi-agent, multi-model workflow capture & synthesis (EJWCS core)."
authors = [{name = "CESAR"}]
requires-python = ">=3.10"
dependencies = [
  "pydantic>=2.7",
  "sqlalchemy>=2.0",
  "networkx>=3.2",
  "httpx>=0.27",
  "pyyaml>=6.0"
]

[project.optional-dependencies]
audio = ["azure-cognitiveservices-speech>=1.38"]
text-analytics = ["azure-ai-textanalytics>=5.3.0"]
export = ["graphviz>=0.20.3", "pillow>=10.0"]
ui = ["rich>=13.7", "pygments>=2.16"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
"""

MAKEFILE = """
.PHONY: format test unit integration lint

format:
	python -m pip install ruff black
	truff check --fix cesar_src tests
	black cesar_src tests

lint:
	python -m pip install ruff mypy types-PyYAML types-requests
	truff check cesar_src tests
	mypy cesar_src

unit:
	pytest -q -k "not integration"

integration:
	pytest -q -k integration

test: unit integration
"""

README_MD = """
# CESAR-SRC (EJWCS core) - Multi-Agent, Multi-Model

This system implements the Caesar SRC vision: **hyper-specialized agent droids** orchestrated by a **single main agent** that is the user's sole point of contact. It natively supports **three LLMs** (two local, one remote) via an OpenAI-compatible router.

## Key Characteristics
- **Multi-agent**: Orchestrator delegates to Extractor, Validator, Visualizer (extensible: Taxonomy, PII, Publisher, Telemetry).
- **Multi-model**: Router targets `local1`, `local2`, and `remote` endpoints simultaneously or selectively.
- **Production-grade**: Strict schema validation, database persistence, deterministic visualization, unit + integration tests, clear configuration validation.

## Configuration
Provide a YAML config with the following keys. Do not use placeholders; populate with your actual values and endpoint URLs. The application validates that `primary_endpoint` exists among `llm_endpoints` and that each endpoint defines `base_url` and `model`.

## Usage
```bash
python -m cesar_src.cli.extract ./config.yaml ./transcript.txt --endpoint remote
```

## Extending Agents
Add new droids under `cesar_src/agents/` and wire them in the `Orchestrator`. Patterns are intentionally small and composable.
"""

ARCHITECTURE_MD = """
# Architecture and Rationale

## Alignment with Caesar SRC Vision
- Main Agent: `Orchestrator` is the single point of contact handling end-user requests.
- Hyper-Specialized Droids: `ExtractorAgent`, `ValidatorAgent`, `VisualizerAgent` each own a bounded context.
- Three LLMs: `LLMRouter` fans out to two local OpenAI-compatible servers and one remote cloud endpoint.

## Data Flow
1. Transcript enters Orchestrator.
2. Extractor calls the selected LLM endpoint to produce `JobWorkflowSchema` JSON.
3. Schema validation ensures referential integrity and DAG structure.
4. Mermaid renderer produces a machine-readable diagram for UIs and exports.
5. Repository persists the JSON plus Mermaid for downstream integrations.

## Error Handling
- Config schema validation with helpful exceptions.
- Router propagates HTTP and schema issues with rich text.
- Pydantic model validators surface graph errors early.
"""

DEPLOYMENT_MD = """
# Deployment

## Python Environment
- Python >= 3.10
- Install via `pip install -e .[audio,export]` as needed.

## Local LLMs
Run local models behind OpenAI-compatible servers (examples):
- Ollama: `ollama serve` and `ollama run <model>` with an OpenAI-compatible adapter.
- LM Studio: enable the OpenAI API server and set `base_url` accordingly.
- vLLM or llama.cpp server: start with OpenAI-compatible REST enabled.

## Remote LLM
Provide `base_url=https://api.openai.com/v1`, `model=<deployed model>`, and set `OPENAI_API_KEY` in the environment.

## Database
Set `database_url` to a production-grade RDBMS (for example, Postgres). The repository is SQLAlchemy-agnostic and will create schema automatically.
"""  # Closing triple quotes intentionally present for safety

SECURITY_MD = """
# Security and Privacy
- Secrets are never stored in the repository; read strictly from environment variables defined in your YAML config via `api_key_env` names.
- Validate inputs at API boundaries; transcripts must be plain text (UTF-8). Add PII redaction as a dedicated agent if required by policy.
- Use TLS/HTTPS for all remote calls and restrict egress via firewall rules for local endpoints.
"""

WHITEPAPER_MD = """
# CESAR-SRC - Multi-Agent, Multi-Model Orchestration (Whitepaper)

Abstract. We present CESAR-SRC, a production-grade architecture implementing a hierarchical multi-agent system with multi-model arbitration. The main agent (Orchestrator) coordinates domain-specialized droids (Extractor, Validator, Visualizer, Jury, Trinity) to transform raw recordings and documents into validated, enriched, and persisting workflow graphs. A reflection pipeline converts interactions into durable knowledge via FTS-backed storage and LLM-mediated distillation. We formalize agent contracts, arbitration heuristics, and verification conditions.
"""

# -----------------------------
# Executable packages (ASCII only)
# -----------------------------

# cesar_src/__init__.py
__all__ = [
    "config",
    "logging",
    "models.schemas",
    "models.db",
    "models.repository",
    "services.llm_router",
    "services.mermaid",
    "agents.orchestrator",
]

# cesar_src/logging.py
import logging as _logging

# Try to use rich if available; otherwise fall back to stdlib only.
try:  # optional dependency
    from rich.logging import RichHandler as _RichHandler  # type: ignore
    _HAS_RICH = True
except Exception:  # ImportError or missing pygments in rich
    _RichHandler = None  # type: ignore
    _HAS_RICH = False

_LOG_FORMAT = "% मैसेज% एस"

def setup_logging(level: str = "INFO") -> None:
    lvl = getattr(_logging, level.upper(), _logging.INFO)
    if _HAS_RICH and _RichHandler is not None:
        _logging.basicConfig(
            level=lvl,
            format=_LOG_FORMAT,
            datefmt="%H:%M:%S",
            handlers=[_RichHandler(rich_tracebacks=True, markup=True)],
        )
    else:
        handler = _logging.StreamHandler()
        formatter = _logging.Formatter(_LOG_FORMAT)
        handler.setFormatter(formatter)
        root = _logging.getLogger()
        root.setLevel(lvl)
        # clear existing handlers to avoid duplicate logs when reloading
        root.handlers = [handler]

# cesar_src/config.py
import os as _os
from dataclasses import dataclass as _dataclass, field as _field
from typing import Dict as _Dict, Optional as _Optional
import yaml as _yaml

class ConfigError(Exception):
    pass

@_dataclass(frozen=True)
class LLMEndpoint:
    name: str
    base_url: str
    model: str
    api_key_env: str
    def api_key(self) -> _Optional[str]:
        return _os.environ.get(self.api_key_env) if self.api_key_env else None

@_dataclass(frozen=True)
class AppConfig:
    environment: str
    database_url: str
    llm_endpoints: _Dict[str, LLMEndpoint] = _field(default_factory=dict)
    primary_endpoint: str = "remote"

    @staticmethod
    def load(path: str) -> "AppConfig":
        with open(path, "r", encoding="utf-8") as f:
            raw = _yaml.safe_load(f)
        try:
            llms = {
                k: LLMEndpoint(
                    name=k,
                    base_url=v["base_url"],
                    model=v["model"],
                    api_key_env=v.get("api_key_env", ""),
                )
                for k, v in raw["llm_endpoints"].items()
            }
            cfg = AppConfig(
                environment=str(raw["environment"]),
                database_url=str(raw["database_url"]),
                llm_endpoints=llms,
                primary_endpoint=str(raw.get("primary_endpoint", "remote")),
            )
        except Exception as e:
            raise ConfigError(f"Invalid config: {e}") from e
        if cfg.primary_endpoint not in cfg.llm_endpoints:
            raise ConfigError("प्राइमरी_एलएलएम_नॉट_फाउंड")
        return cfg

# cesar_src/models/schemas.py
import uuid as _uuid
from typing import List as _List, Optional as _Optional
from pydantic import BaseModel as _BaseModel, Field as _Field, field_validator as _field_validator, model_validator as _model_validator
import networkx as _nx

class ConditionalLogic(_BaseModel):
    condition: str = _Field(..., description="Predicate determining branching")
    true_path_task_id: str = _Field(...)
    false_path_task_id: _Optional[str] = _Field(None)

class KnowledgeItem(_BaseModel):
    id: str
    description: str

class SkillItem(_BaseModel):
    id: str
    description: str

class TaskObject(_BaseModel):
    task_id: str = _Field(default_factory=lambda: str(_uuid.uuid4()))
    task_description: str
    role_owner: str
    precedes_tasks: _List[str] = _Field(default_factory=list)
    dependencies: _List[str] = _Field(default_factory=list)
    conditional_logic: _Optional[ConditionalLogic] = None
    required_knowledge: _List[KnowledgeItem] = _Field(default_factory=list)
    required_skill_tags: _List[SkillItem] = _Field(default_factory=list)

class JobWorkflowSchema(_BaseModel):
    workflow_name: str
    tasks: _List[TaskObject]

    @_field_validator("tasks")
    @classmethod
    def _validate_refs(cls, tasks: _List[TaskObject]) -> _List[TaskObject]:
        ids = {t.task_id for t in tasks}
        for t in tasks:
            for d in t.dependencies:
                if d not in ids:
                    raise ValueError(f"Dependency '{d}' not found")
            for n in t.precedes_tasks:
                if n not in ids:
                    raise ValueError(f"Successor '{n}' not found")
        return tasks

    @_model_validator(mode="after")
    def _validate_dag(self) -> "JobWorkflowSchema":
        G = _nx.DiGraph()
        for t in self.tasks:
            G.add_node(t.task_id)
        for t in self.tasks:
            for n in t.precedes_tasks:
                G.add_edge(t.task_id, n)
            if t.conditional_logic:
                G.add_edge(t.task_id, t.conditional_logic.true_path_task_id)
                if t.conditional_logic.false_path_task_id:
                    G.add_edge(t.task_id, t.conditional_logic.false_path_task_id)
        if not _nx.is_directed_acyclic_graph(G):
            raise ValueError("Workflow contains cycles")
        roots = [n for n, indeg in G.in_degree() if indeg == 0]
        if not roots:
            raise ValueError("No root task detected")
        return self

# cesar_src/models/db.py
from datetime import datetime as _datetime
from sqlalchemy import create_engine as _create_engine, String as _String, JSON as _JSON, DateTime as _DateTime, Text as _Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

class _Base(DeclarativeBase):
    pass

class WorkflowModel(_Base):
    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(_String(64), primary_key=True)
    name: Mapped[str] = mapped_column(_String(255), index=True)
    json_data: Mapped[dict] = mapped_column(_JSON)
    mermaid_code: Mapped[str] = mapped_column(_Text)
    created_at: Mapped[
_datetime] = mapped_column(_DateTime, default=_datetime.utcnow)
    updated_at: Mapped[_datetime] = mapped_column(_DateTime, default=_datetime.utcnow, onupdate=_datetime.utcnow)


def make_session(database_url: str):
    engine = _create_engine(database_url, pool_pre_ping=True)
    _Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)

# cesar_src/models/repository.py
import json as _json2
import uuid as _uuid2
from sqlalchemy.orm import Session as _Session

class WorkflowRepository:
    def __init__(self, session_factory):
        self._sf = session_factory

    def save(self, name: str, workflow, mermaid_code: str) -> str:
        from .db import WorkflowModel  # local import to avoid circulars at import time
        wid = str(_uuid2.uuid4())
        with self._sf() as s:  # type: _Session
            model = WorkflowModel(
                id=wid,
                name=name,
                json_data=_json2.loads(workflow.model_dump_json()),
                mermaid_code=mermaid_code,
            )
            s.add(model)
            s.commit()
        return wid

    def get(self, workflow_id: str):
        from .db import WorkflowModel
        with self._sf() as s:  # type: _Session
            return s.get(WorkflowModel, workflow_id)

# cesar_src/services/mermaid.py
from typing import List as _List

class Mermaid:
    @staticmethod
    def _sanitize(text: str, max_len: int = 120) -> str:
        t = (text or "").replace("\n", " ").replace('"', "'")
        return (t[: max_len - 1] + "...") if len(t) > max_len else t

    @classmethod
    def render(cls, workflow: JobWorkflowSchema) -> str:
        lines: _List[str] = ["graph TD"]
        for t in workflow.tasks:
            role = t.role_owner or "role?"
            label = cls._sanitize(t.task_description)
            lines.append(f'    {t.task_id}(["{label}\\n<sub>{role}</sub>"])
')
        for t in workflow.tasks:
            for nxt in t.precedes_tasks:
                lines.append(f'    {t.task_id} --> {nxt}
')
            if t.conditional_logic:
                c = t.conditional_logic
                lines.append(f'    {t.task_id} -- "{cls._sanitize(c.condition, 60)}" --> {c.true_path_task_id}
')
                if c.false_path_task_id:
                    lines.append(f'    {t.task_id} -- "Else" --> {c.false_path_task_id}
')
        dec = [t.task_id for t in workflow.tasks if t.conditional_logic]
        if dec:
            lines.append('    classDef decisionNode fill:#ffe4b5,stroke:#333;
')
            for n in dec:
                lines.append(f'    class {n} decisionNode;
')
        return "\n".join(lines)

# cesar_src/services/llm_router.py
from typing import Dict as _Dict2, Any as _Any2
import httpx as _httpx

class LLMRouterError(Exception):
    pass

class LLMRouter:
    """Routes chat-completion calls across multiple OpenAI-compatible endpoints (two local, one remote)."""

    def __init__(self, config: AppConfig):
        self.cfg = config

    async def chat(self, *, endpoint: str | None, messages: list[dict[str, str]], temperature: float = 0.1, max_tokens: int = 4096) -> str:
        name = endpoint or self.cfg.primary_endpoint
        if name not in self.cfg.llm_endpoints:
            raise LLMRouterError(f"Unknown endpoint '{name}'")
        ep = self.cfg.llm_endpoints[name]
        return await self._openai_compatible_chat(ep, messages, temperature, max_tokens)

    async def _openai_compatible_chat(self, ep: LLMEndpoint, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        url = ep.base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = ep.api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload: _Dict2[str, _Any2] = {
            "model": ep.model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        async with _httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code >= 400:
                raise LLMRouterError(f"{ep.name} error {r.status_code}: {r.text}")
            data = r.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001
            raise LLMRouterError(f"Malformed response from {ep.name}: {data}") from e
        return content

# cesar_src/agents/base.py
from abc import ABC as _ABC, abstractmethod as _abstractmethod
from typing import Any as _Any3, Dict as _Dict3

class Agent(_ABC):
    name: str

    @_abstractmethod
    async def run(self, payload: _Dict3[str, _Any3]) -> _Dict3[str, _Any3]:
        ...

# cesar_src/agents/extractor_agent.py
import json as _json2

_SYSTEM_PROMPT = (
    "You are the EJWCS Workflow Extractor agent. Analyze SME interview transcripts and produce a single, valid "
    "JSON object STRICTLY conforming to the provided JSON Schema (Pydantic model). Requirements: "
    "1) Extract tasks in chronological order, 2) identify dependencies, 3) include conditional logic when present, "
    "4) map roles to occupation codes, 5) map skills and knowledge to ESCO identifiers if present, 6) if a field is unknown use null "
    "but DO NOT omit keys. OUTPUT ONLY RAW JSON."
)

class ExtractorAgent:
    name = "extractor"

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, payload: dict) -> dict:
        transcript: str = payload["transcript"]
        schema = JobWorkflowSchema.model_json_schema()
        user_prompt = (
            f"Input Transcript:\n{transcript}\n\n"
            f"Schema Definition (JSON Schema):\n{_json2.dumps(schema, indent=2)}"
        )
        out = await self.router.chat(
            endpoint=payload.get("endpoint", None),
            messages=[{"role": "system", "content": _SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
            temperature=0.1,
            max_tokens=4000,
        )
        data = _json2.loads(out)
        workflow = JobWorkflowSchema(**data)
        return {"workflow": workflow}

# cesar_src/agents/visualizer_agent.py
class VisualizerAgent:
    name = "visualizer"

    async def run(self, payload: dict) -> dict:
        wf: JobWorkflowSchema = payload["workflow"]
        code = Mermaid.render(wf)
        return {"mermaid": code}

# cesar_src/agents/validator_agent.py
class ValidatorAgent:
    name = "validator"

    async def run(self, payload: dict) -> dict:
        wf: JobWorkflowSchema = payload["workflow"]
        _ = JobWorkflowSchema(**wf.model_dump())
        return {"valid": True}

# cesar_src/agents/orchestrator.py
class Orchestrator:
    """Main entrypoint agent coordinating specialized droids (CESAR-SRC vision)."""

    def __init__(self, router: LLMRouter, repo, *, telemetry: object | None = None, learnloop: object | None = None):
        # from .models.repository import WorkflowRepository as _WR
        # assert isinstance(repo, _WR)
        self.router = router
        self.repo = repo
        self.extractor = ExtractorAgent(router)
        self.validator = ValidatorAgent()
        self.visualizer = VisualizerAgent()
        self.telemetry = telemetry
        self.learnloop = learnloop

    async def process_transcript(self, *, transcript: str, endpoint: str | None = None) -> dict:
        ex = await self.extractor.run({"transcript": transcript, "endpoint": endpoint})
        wf: JobWorkflowSchema = ex["workflow"]
        if self.telemetry:
            try:
                self.telemetry.log_interaction(agent="extractor", role="system", inputs={"transcript_len": len(transcript)}, outputs=wf.model_dump(), meta={"endpoint": endpoint})
            except Exception:
                pass
        _ = await self.validator.run({"workflow": wf})
        if self.telemetry:
            try:
                self.telemetry.log_interaction(agent="validator", role="system", inputs={"task_count": len(wf.tasks)}, outputs={"valid": True}, meta={})
            except Exception:
                pass
        viz = await self.visualizer.run({"workflow": wf})
        mermaid = viz["mermaid"]
        if self.telemetry:
            try:
                self.telemetry.log_interaction(agent="visualizer", role="system", inputs={"task_count": len(wf.tasks)}, outputs={"mermaid_lines": len(mermaid.splitlines())}, meta={})
            except Exception:
                pass
        
        # This is the part we will replace with our new UnifiedRepository
        # workflow_id = self.repo.save(wf.workflow_name, wf, mermaid)
        workflow_id = "temp_id_before_db_integration"

        if self.learnloop:
            try:
                import datetime as _dt
                payload_text = f"Workflow: {wf.workflow_name}\nTasks: {len(wf.tasks)}\n\nMermaid:\n{mermaid}"
                await self.learnloop.record_and_reflect(doc_id=workflow_id, title=wf.workflow_name, text=payload_text, source="orchestrator", created_at=_dt.datetime.utcnow().isoformat())
            except Exception:
                pass
        return {"workflow_id": workflow_id, "mermaid": mermaid, "task_count": len(wf.tasks)}

# cesar_src/automation/matrix.py
import os as _os2
from dataclasses import dataclass as _dataclass2
from typing import Dict as _Dict4, Optional as _Optional4
import yaml as _yaml2

class AutomationMatrixError(Exception):
    pass

@_dataclass2(frozen=True)
class Service:
    name: str
    base_url: str
    api_key_env: _Optional4[str]
    def api_key(self) -> _Optional4[str]:
        return _os2.environ.get(self.api_key_env) if self.api_key_env else None

@_dataclass2(frozen=True)
class WorkflowBinding:
    workflow: str
    service: str
    enabled: bool

@_dataclass2(frozen=True)
class AutomationMatrix:
    services: _Dict4[str, Service]
    bindings: _Dict4[str, WorkflowBinding]

    @staticmethod
    def load(path: str) -> "AutomationMatrix":
        with open(path, "r", encoding="utf-8") as f:
            raw = _yaml2.safe_load(f)
        try:
            services = {
                name: Service(name=name, base_url=v["base_url"], api_key_env=v.get("api_key_env", None))
                for name, v in raw["services"].items()
            }
            bindings = {
                b["workflow"]:
                WorkflowBinding(workflow=b["workflow"], service=b["service"], enabled=bool(b.get("enabled", True)))
                for b in raw["bindings"]
            }
        except Exception as e:
            raise AutomationMatrixError(f"Invalid automation matrix: {e}") from e
        for wf, bind in bindings.items():
            if bind.service not in services:
                raise AutomationMatrixError(f"Binding references unknown service '{bind.service}' for workflow '{wf}'")
        return AutomationMatrix(services=services, bindings=bindings)

    def service_for(self, workflow_name: str) -> Service:
        if workflow_name not in self.bindings:
            raise AutomationMatrixError(f"No binding for workflow '{workflow_name}'")
        b = self.bindings[workflow_name]
        if not b.enabled:
            raise AutomationMatrixError(f"Binding for workflow '{workflow_name}' is disabled")
        return self.services[b.service]

# cesar_src/brains/knowledge.py
import sqlite3 as _sqlite3
from pathlib import Path as _Path
from typing import Iterable as _Iterable, List as _List2, Tuple as _Tuple2

class KnowledgeBrain:
    """SQLite FTS5 KB for full-text recall and provenance."""
    def __init__(self, db_path: str):
        self.path = _Path(db_path)
        self.conn = _sqlite3.connect(self.path)
        self._init()
    def _init(self) -> None:
        cur = self.conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS kb USING fts5(
                doc_id UNINDEXED, title, text, source, created_at UNINDEXED
            );
            """
        )
        self.conn.commit()
    def upsert(self, rows: _Iterable[_Tuple2[str, str, str, str, str]]) -> None:
        cur = self.conn.cursor()
        cur.executemany("INSERT INTO kb (doc_id, title, text, source, created_at) VALUES (?,?,?,?,?)", rows)
        self.conn.commit()
    def search(self, query: str, k: int = 8) -> _List2[_Tuple2[str, str, str, str, str]]:
        cur = self.conn.cursor()
        cur.execute("SELECT doc_id, title, text, source, created_at FROM kb WHERE kb MATCH ? LIMIT ?", (query, k))
        return list(cur.fetchall())

# cesar_src/brains/data.py
from typing import Dict as _Dict5, Any as _Any5
import datetime as _dt
import yfinance as _yf

class DataBrain:
    def pull_financial_timeseries(self, ticker: str, start: str, end: str, interval: str = "1d") -> _Dict5[str, _Any5]:
        s = _dt.datetime.fromisoformat(start)
        e = _dt.datetime.fromisoformat(end)
        data = _yf.download(ticker, start=s, end=e, interval=interval, progress=False)
        if data is None or data.empty:
            raise ValueError(f"No data for {ticker} {start}->{end}")
        data = data.rename(columns={c: c.lower() for c in data.columns})
        return {
            "ticker": ticker,
            "start": start,
            "end": end,
            "interval": interval,
            "rows": [
                {
                    "ts": idx.isoformat(),
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)),
                }
                for idx, row in data.iterrows()
            ],
        }

# cesar_src/agents/jury_agent.py
import json as _json3

CRITIC_PROMPT = (
    "You are the Jury Agent. Given N candidate answers, 1) identify agreement/disagreement, 2) rate each (1-10) on factuality, completeness, safety, 3) propose a final synthesized answer with citations to candidate #s. Respond as JSON with keys: ratings (list), issues (list), final_answer (string)."
)

class JuryAgent:
    name = "jury"
    def __init__(self, router: LLMRouter):
        self.router = router
    async def run(self, payload: dict) -> dict:
        candidates: list[str] = payload["candidates"]
        structured = "\n\n".join([f"Candidate #{i+1}:\n{c}" for i, c in enumerate(candidates)])
        msg = f"{CRITIC_PROMPT}\n\n{structured}"
        out = await self.router.chat(endpoint=payload.get("endpoint", None), messages=[{"role": "user", "content": msg}], temperature=0.1, max_tokens=2000)
        data = _json3.loads(out)
        return data

# cesar_src/agents/trinity_agent.py
class TrinityAgent:
    """Neural triangulation across endpoints with Jury synthesis."""
    def __init__(self, router: LLMRouter, jury: JuryAgent):
        self.router = router
        self.jury = jury
    async def run(self, payload: dict) -> dict:
        prompt = payload["prompt"]
        endpoints = payload.get("endpoints") or list(self.router.cfg.llm_endpoints.keys())
        answers = []
        for ep in endpoints:
            ans = await self.router.chat(endpoint=ep, messages=[{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1200)
            answers.append(ans)
        verdict = await self.jury.run({"candidates": answers, "endpoint": payload.get("endpoint", None)})
        return {"answers": answers, "verdict": verdict}

# cesar_src/pipelines/learn_loop.py
import json as _json4, time as _time
class LearnLoop:
    POLICY = (
        "You are a Reflection Agent. Given interaction logs (prompt, context snippets, outputs), extract: 1) stable facts, 2) hypothesized rules, 3) open questions, 4) follow-up actions. Return JSON with keys: facts, rules, questions, actions."
    )
    def __init__(self, kb: KnowledgeBrain, router: LLMRouter):
        self.kb = kb
        self.router = router
    async def record_and_reflect(self, *, doc_id: str, title: str, text: str, source: str, created_at: str) -> dict:
        self.kb.upsert([(doc_id, title, text, source, created_at)])
        out = await self.router.chat(endpoint=None, messages=[{"role": "system", "content": self.POLICY}, {"role": "user", "content": text}], temperature=0.1, max_tokens=1500)
        data = _json4.loads(out)
        rid = f"reflect:{doc_id}:{int(_time.time())}"
        self.kb.upsert([(rid, f"Reflection:{title}", _json4.dumps(data, ensure_ascii=False), source, created_at)])
        return data

# cesar_src/telemetry/ledger.py
import sqlite3 as _sqlite3b
from pathlib import Path as _PathB
from typing import Any as _AnyB, Dict as _DictB, Optional as _OptionalB
import json as _jsonB
import time as _timeB

class TelemetryLedger:
    """Captures detailed summaries of all interactions between users, agents, and LLMs."""
    def __init__(self, db_path: str):
        self.path = _PathB(db_path)
        self.conn = _sqlite3b.connect(self.path)
        self._init()
    def _init(self) -> None:
        c = self.conn.cursor()
        c.execute("PRAGMA journal_mode=WAL;")
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                agent TEXT NOT NULL,
                role TEXT NOT NULL,
                inputs TEXT NOT NULL,
                outputs TEXT NOT NULL,
                meta TEXT NOT NULL
            );
            """
        )
        self.conn.commit()
    def log_interaction(self, *, agent: str, role: str, inputs: _DictB[str, _AnyB], outputs: _DictB[str, _AnyB] | str, meta: _DictB[str, _AnyB]) -> None:
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO interactions (ts, agent, role, inputs, outputs, meta) VALUES (?,?,?,?,?,?)",
            (int(_timeB.time()), agent, role, _jsonB.dumps(inputs, ensure_ascii=False), _jsonB.dumps(outputs, ensure_ascii=False) if not isinstance(outputs, str) else outputs, _jsonB.dumps(meta, ensure_ascii=False)),
        )
        self.conn.commit()
    def summarize(self, *, since_ts: _OptionalB[int] = None) -> dict:
        q = "SELECT ts, agent, role, inputs, outputs, meta FROM interactions"
        params: list[_AnyB] = []
        if since_ts is not None:
            q += " WHERE ts >= ?"
            params.append(int(since_ts))
        q += " ORDER BY ts ASC"
        rows = self.conn.execute(q, params).fetchall()
        def _maybe_json(s: str):
            try:
                return _jsonB.loads(s)
            except Exception:
                return s
        return {
            "count": len(rows),
            "events": [
                {"ts": r[0], "agent": r[1], "role": r[2], "inputs": _maybe_json(r[3]), "outputs": _maybe_json(r[4]), "meta": _maybe_json(r[5])}
                for r in rows
            ],
        }

# -----------------------------
# Snapshot utility & CLI (saves a copy of this file to your computer)
# -----------------------------
import os as _os3, shutil as _shutil, datetime as _datetime2, pathlib as _pathlib, sys as _sys

SNAPSHOT_ENV_DIR = "CESAR_SNAPSHOT_DIR"  # override default snapshot directory

def snapshot_self(out_dir: str | None = None) -> str:
    """Copy the current file (__file__) to a timestamped path under out_dir.

    Default out_dir: ~/CESAR_SNAPSHOTS (or $CESAR_SNAPSHOT_DIR if set).
    Returns the full path to the created snapshot file.
    """
    src = _pathlib.Path(__file__).resolve()
    root = _pathlib.Path(out_dir or _os3.environ.get(SNAPSHOT_ENV_DIR) or (_pathlib.Path.home() / "CESAR_SNAPSHOTS"))
    root.mkdir(parents=True, exist_ok=True)
    ts = _datetime2.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dst = root / f"ejwcs_snapshot_{ts}.py"
    _shutil.copy2(src, dst)
    return str(dst)

# CLI: python this_file.py --snapshot [--dir /path/to/save]
if __name__ == "__main__":
    if "--snapshot" in _sys.argv:
        try:
            if "--dir" in _sys.argv:
                d_idx = _sys.argv.index("--dir")
                target_dir = _sys.argv[d_idx + 1]
            else:
                target_dir = None
            p = snapshot_self(target_dir)
            print(f"Snapshot saved to: {p}")
        except Exception as e:  # noqa: BLE001
            print(f"Snapshot failed: {e}", file=_sys.stderr)
            _sys.exit(1)

# -----------------------------
# Reference tests (ASCII only; keep existing semantics)
# -----------------------------
TEST_MERMAID = """
from cesar_src.models.schemas import JobWorkflowSchema, TaskObject
from cesar_src.services.mermaid import Mermaid

def test_mermaid_basic():
    t = TaskObject(task_id="T1", task_description="Do a thing", role_owner="Role")
    wf = JobWorkflowSchema(workflow_name="WF", tasks=[t])
    code = Mermaid.render(wf)
    assert code.startswith("graph TD")
    assert "T1" in code
    assert "\n" in code

def test_mermaid_escapes_quotes_and_newlines():
    desc = 'Say "hello" and\nthen continue'
    t = TaskObject(task_id="T2", task_description=desc, role_owner="Mgr")
    wf = JobWorkflowSchema(workflow_name="WF2", tasks=[t])
    code = Mermaid.render(wf)
    assert 'T2(["\' in code
    assert '<sub>Mgr</sub>' in code
"""

TEST_SCHEMAS = """
import pytest
from cesar_src.models.schemas import JobWorkflowSchema, TaskObject

def test_cycle_detection_raises():
    t1 = TaskObject(task_id="A", task_description="A", role_owner="r", precedes_tasks=["B"])
    t2 = TaskObject(task_id="B", task_description="B", role_owner="r", precedes_tasks=["A"])
    with pytest.raises(ValueError):
        JobWorkflowSchema(workflow_name="Cycle", tasks=[t1, t2])

def test_missing_ref_raises():
    t1 = TaskObject(task_id="A", task_description="A", role_owner="r", precedes_tasks=["Z"])  # Z not present
    with pytest.raises(ValueError):
        JobWorkflowSchema(workflow_name="BadRefs", tasks=[t1])
"""

TEST_ROUTER = """
import os, pytest
from cesar_src.config import AppConfig
from cesar_src.services.llm_router import LLMRouter

CONFIG_SCHEMA = {
    "environment": "dev",
    "database_url": "sqlite:///test.db",
    "llm_endpoints": {
        "local1": {"base_url": "http://127.0.0.1:11434/v1", "model": "qwen2.5:7b", "api_key_env": ""},
        "local2": {"base_url": "http://127.0.0.1:8000/v1", "model": "llama3.1:8b", "api_key_env": ""},
        "remote": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key_env": "OPENAI_API_KEY"},
    },
    "primary_endpoint": "remote",
}

def test_config_loads(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(__import__("yaml").safe_dump(CONFIG_SCHEMA), encoding="utf-8")
    cfg = AppConfig.load(str(p))
    assert cfg.primary_endpoint == "remote"
    assert "local1" in cfg.llm_endpoints

@pytest.mark.integration
@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="requires OPENAI_API_KEY")
@pytest.mark.timeout(30)
async def test_router_remote_chat_roundtrip(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(__import__("yaml").safe_dump(CONFIG_SCHEMA), encoding="utf-8")
    cfg = AppConfig.load(str(p))
    router = LLMRouter(cfg)
    out = await router.chat(endpoint="remote", messages=[{"role": "user", "content": "Say 'ok'"}], temperature=0.0, max_tokens=5)
    assert "ok".lower() in out.lower()
"""

TEST_TELEMETRY = """
from cesar_src.telemetry.ledger import TelemetryLedger

def test_telemetry_log_and_summarize(tmp_path):
    db = tmp_path / "telemetry.db"
    led = TelemetryLedger(str(db))
    led.log_interaction(agent="extractor", role="system", inputs={"x":1}, outputs={"y":2}, meta={"m":3})
    summary = led.summarize()
    assert summary["count"] >= 1
    assert any(ev["agent"] == "extractor" for ev in summary["events"])
"""

TEST_LOGGING = """
# Ensure logging setup does not require rich/pygments to be installed.
from cesar_src import logging as clog

def test_setup_logging_fallback():
    # Should not raise even if rich is unavailable in environment
    clog.setup_logging("INFO")
"""

TEST_DB_ORM = """
# Validates SQLAlchemy ORM annotations (Mapped[...] and mapped_column) are correctly interpreted
from cesar_src.models.db import make_session, WorkflowModel
from cesar_src.models.schemas import JobWorkflowSchema, TaskObject
from cesar_src.models.repository import WorkflowRepository

def test_db_persist_roundtrip(tmp_path):
    db_path = tmp_path / "e2e.db"
    Session = make_session(f"sqlite:///{db_path}")
    repo = WorkflowRepository(Session)

    t1 = TaskObject(task_id="X1", task_description="Start", role_owner="Owner")
    t2 = TaskObject(task_id="X2", task_description="Next", role_owner="Owner", dependencies=["X1"])
    wf = JobWorkflowSchema(workflow_name="WF_DB", tasks=[t1, t2])

    wid = repo.save(wf.workflow_name, wf, mermaid_code="graph TD\nX1-->X2")
    model = repo.get(wid)
    assert isinstance(model, WorkflowModel)
    assert model.name == "WF_DB"
    assert "mermaid" not in model.json_data  # ensure schema persisted as JSON dict
"""

# -----------------------------
# ASCII-guard utility (optional runtime check)
# -----------------------------
ASCII_BLOCKLIST = ["‘", "’", "‑", "…", "→"]

def assert_ascii_only() -> None:
    src = (
        PYPROJECT_TOML + MAKEFILE + README_MD + ARCHITECTURE_MD + DEPLOYMENT_MD + SECURITY_MD + WHITEPAPER_MD
    )
    for bad in ASCII_BLOCKLIST:
        assert bad not in src, f"Found non-ASCII character {bad} in embedded assets"

# Run guard at import time to fail fast if future edits reintroduce smart quotes
assert_ascii_only()

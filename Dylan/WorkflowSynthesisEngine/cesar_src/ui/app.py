"""FastAPI-based GUI for the Workflow Synthesis Engine."""

from __future__ import annotations

import json
import os
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

from ..agents.orchestrator import Orchestrator
from ..config import AppConfig
from ..integrations import (
    AutogenWorkflowBridge,
    AutomationMatrixRecommender,
    LivingDataBrainRepository,
    MasterJobTreeEnricher,
    SkillNodeMatcher,
)
from ..services.llm_router import LLMRouter


class InMemoryRepository:
    """Session-scoped repository storing workflow runs for the GUI."""

    def __init__(self) -> None:
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._order: list[str] = []

    def record_workflow(
        self,
        *,
        workflow_id: str,
        workflow: Any,
        transcript: str,
        mermaid: str,
        autogen_script_path: str | None,
        skill_links: list[dict] | None,
        automation_links: list[dict] | None,
    ) -> int:
        identifier = len(self._storage) + 1
        record = {
            "workflow_id": workflow_id,
            "workflow_name": workflow.workflow_name,
            "workflow": workflow.model_dump(),
            "transcript": transcript,
            "mermaid": mermaid,
            "autogen_script_path": autogen_script_path,
            "skill_links": skill_links or [],
            "automation_links": automation_links or [],
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        key = str(identifier)
        self._storage[key] = record
        self._order.append(key)
        return identifier

    def get(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        return self._storage.get(workflow_id)

    def fetch_recent_runs(self, limit: int = 25) -> list[dict]:
        rows: list[dict] = []
        for key in reversed(self._order[-limit:]):
            entry = self._storage[key]
            rows.append(
                {
                    "workflow_id": key,
                    "workflow_name": entry.get("workflow_name", key),
                    "created_at": entry.get("created_at", ""),
                    "task_count": len(entry.get("workflow", {}).get("tasks", [])),
                    "autogen_script_path": entry.get("autogen_script_path"),
                }
            )
        return rows


def _build_repository(cfg: AppConfig):
    if cfg.living_data_brain_db:
        return LivingDataBrainRepository(cfg.living_data_brain_db)
    return InMemoryRepository()


def _build_enricher(cfg: AppConfig):
    if cfg.master_job_tree_root:
        return MasterJobTreeEnricher(cfg.master_job_tree_root)
    return None


def _build_skill_matcher(cfg: AppConfig):
    if cfg.skill_node_registry:
        return SkillNodeMatcher(cfg.skill_node_registry)
    return None


def _build_automation_bridge(cfg: AppConfig):
    if cfg.autogen_creator_path:
        workflows_dir = cfg.autogen_workflows_dir or Path(cfg.autogen_creator_path).resolve().parent / "workflows"
        return AutogenWorkflowBridge(Path(cfg.autogen_creator_path), Path(workflows_dir))
    return None


def _build_automation_recommender(cfg: AppConfig):
    if cfg.automation_matrix_root:
        return AutomationMatrixRecommender(cfg.automation_matrix_root)
    return None


def _load_app_state():
    config_path = Path(os.getenv("CESAR_CONFIG_PATH", "config.yaml"))
    cfg = AppConfig.load(str(config_path))
    repo = _build_repository(cfg)
    router = LLMRouter(cfg)
    orchestrator = Orchestrator(
        router,
        repo,
        enricher=_build_enricher(cfg),
        automation_bridge=_build_automation_bridge(cfg),
        skill_matcher=_build_skill_matcher(cfg),
        automation_recommender=_build_automation_recommender(cfg),
    )
    return orchestrator, repo, cfg


app = FastAPI(title="Workflow Synthesis GUI")


@app.on_event("startup")
async def _startup() -> None:
    orchestrator, repo, cfg = _load_app_state()
    app.state.orchestrator = orchestrator
    app.state.repo = repo
    app.state.config = cfg


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    cfg: AppConfig = app.state.config
    repo = app.state.repo
    recent = _recent_runs(repo)
    return HTMLResponse(
        _render_form(
            endpoints=list(cfg.llm_endpoints.keys()),
            selected_endpoint=cfg.primary_endpoint,
            history=recent,
        )
    )


@app.post("/run", response_class=HTMLResponse)
async def run_transcript(
    transcript: str = Form(...),
    endpoint: str | None = Form(None),
) -> HTMLResponse:
    orchestrator: Orchestrator = app.state.orchestrator
    repo = app.state.repo
    cfg: AppConfig = app.state.config
    endpoints = list(cfg.llm_endpoints.keys())
    selected_endpoint = endpoint or cfg.primary_endpoint
    try:
        result = await orchestrator.process_transcript(transcript=transcript, endpoint=endpoint or None)
        entry = _get_entry(repo, result["workflow_id"], transcript, result)
        content = _render_form(
            transcript=transcript,
            result_json=json.dumps(result, indent=2),
            mermaid=result.get("mermaid", ""),
            endpoints=endpoints,
            selected_endpoint=selected_endpoint,
            history=_recent_runs(repo),
            current_entry=entry,
            skill_links=result.get("skill_links", []),
            automation_links=result.get("automation_links", []),
        )
    except Exception as exc:  # noqa: BLE001
        content = _render_form(
            transcript=transcript,
            error=str(exc),
            endpoints=endpoints,
            selected_endpoint=selected_endpoint,
            history=_recent_runs(repo),
        )
    return HTMLResponse(content)


@app.get("/history/{workflow_id}", response_class=HTMLResponse)
async def view_history(workflow_id: str) -> HTMLResponse:
    repo = app.state.repo
    cfg: AppConfig = app.state.config
    entry = _get_entry(repo, workflow_id)
    if not entry:
        return HTMLResponse(_render_form(error=f"Workflow '{workflow_id}' not found."))
    result_payload = entry.get("result") or {
        "workflow_id": workflow_id,
        "mermaid": entry.get("mermaid", ""),
        "task_count": len(entry.get("workflow", {}).get("tasks", [])),
        "skill_links": entry.get("skill_links", []),
        "automation_links": entry.get("automation_links", []),
    }
    return HTMLResponse(
        _render_form(
            transcript=entry.get("transcript", ""),
            result_json=json.dumps(result_payload, indent=2),
            mermaid=entry.get("mermaid", ""),
            endpoints=list(cfg.llm_endpoints.keys()),
            selected_endpoint=cfg.primary_endpoint,
            history=_recent_runs(repo),
            current_entry=entry,
            skill_links=result_payload.get("skill_links", []),
            automation_links=result_payload.get("automation_links", []),
        )
    )


@app.get("/download/{workflow_id}")
async def download(workflow_id: str) -> JSONResponse:
    repo = app.state.repo
    entry = _get_entry(repo, workflow_id)
    if not entry:
        return JSONResponse({"error": "not_found"}, status_code=404)
    payload = {
        "workflow": entry.get("workflow", {}),
        "mermaid": entry.get("mermaid", ""),
        "metadata": {
            "workflow_id": entry.get("workflow_id", workflow_id),
            "workflow_name": entry.get("workflow_name", workflow_id),
            "created_at": entry.get("created_at"),
        },
        "skill_links": entry.get("skill_links", []),
        "automation_links": entry.get("automation_links", []),
    }
    return JSONResponse(payload)


def _recent_runs(repo) -> list[Dict[str, Any]]:
    if hasattr(repo, "fetch_recent_runs"):
        return list(repo.fetch_recent_runs())  # type: ignore[arg-type]
    if isinstance(repo, InMemoryRepository):
        return repo.fetch_recent_runs()
    return []


def _get_entry(
    repo,
    workflow_id: str,
    transcript: str | None = None,
    result: Dict[str, Any] | None = None,
) -> Optional[Dict[str, Any]]:
    if hasattr(repo, "get"):
        entry = repo.get(workflow_id)
        if entry is not None:
            return entry
    if isinstance(repo, InMemoryRepository):
        entry = repo.get(str(workflow_id))
        if entry is not None:
            return entry
    if result is not None:
        return {
            "workflow_id": workflow_id,
            "workflow_name": result.get("workflow_id", workflow_id),
            "workflow": result,
            "transcript": transcript or "",
            "mermaid": result.get("mermaid", ""),
            "autogen_script_path": result.get("autogen_script_path"),
            "skill_links": result.get("skill_links", []),
            "automation_links": result.get("automation_links", []),
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
    return None


def _render_form(
    *,
    transcript: str = "",
    result_json: str | None = None,
    mermaid: str | None = None,
    error: str | None = None,
    endpoints: list[str] | None = None,
    selected_endpoint: str | None = None,
    history: list[Dict[str, Any]] | None = None,
    current_entry: Dict[str, Any] | None = None,
    skill_links: list[dict] | None = None,
    automation_links: list[dict] | None = None,
) -> str:
    transcript_value = escape(transcript)
    error_html = f"<div class=\"error\">{escape(error)}</div>" if error else ""
    result_html = f"<pre>{escape(result_json)}</pre>" if result_json else ""
    mermaid_html = f"<div class=\"mermaid\">{escape(mermaid)}</div>" if mermaid else ""
    endpoint_options = ""
    for ep in endpoints or []:
        selected = " selected" if selected_endpoint == ep else ""
        endpoint_options += f"<option value=\"{escape(ep)}\"{selected}>{escape(ep)}</option>"
    history_rows = "".join(
        f"<tr><td>{escape(item.get('created_at', ''))}</td>"
        f"<td>{escape(item.get('workflow_id', ''))}</td>"
        f"<td>{escape(item.get('workflow_name', ''))}</td>"
        f"<td><a href=\"/history/{escape(item.get('workflow_id', ''))}\">View</a></td>"
        f"<td><a href=\"/download/{escape(item.get('workflow_id', ''))}\" target=\"_blank\">Download JSON</a></td></tr>"
        for item in history or []
    )
    history_table = (
        "<table><thead><tr><th>Timestamp</th><th>ID</th><th>Name</th><th colspan=2>Actions</th></tr></thead>"
        f"<tbody>{history_rows}</tbody></table>"
        if history_rows
        else "<p class=\"placeholder\">No workflows run yet.</p>"
    )
    current_overview = ""
    if current_entry:
        current_overview = "<section class=\"summary\">"
        current_overview += f"<h2>Current Workflow: {escape(current_entry.get('workflow_name', current_entry.get('workflow_id', '')))}</h2>"
        current_overview += "<ul>"
        current_overview += f"<li><strong>ID:</strong> {escape(current_entry.get('workflow_id', ''))}</li>"
        current_overview += f"<li><strong>Created:</strong> {escape(current_entry.get('created_at', ''))}</li>"
        workflow = current_entry.get("workflow", {})
        task_count = len(workflow.get("tasks", [])) if isinstance(workflow, dict) else current_entry.get("task_count", "-")
        current_overview += f"<li><strong>Task Count:</strong> {task_count}</li>"
        current_overview += "</ul>"
        current_overview += "</section>"

    skill_rows = "".join(
        f"<tr><td>{escape(link.get('task_id', ''))}</td><td>{escape(link.get('skill_id', ''))}</td><td>{escape(link.get('skill_name', ''))}</td><td>{escape(str(link.get('confidence', '')))}</td><td>{escape(link.get('namespace', ''))}</td></tr>"
        for link in skill_links or []
    )
    skill_table = (
        "<section class=\"panel\"><h3>Skill Node Matches</h3><table><thead><tr><th>Task</th><th>Skill ID</th><th>Name</th><th>Confidence</th><th>Namespace</th></tr></thead>"
        f"<tbody>{skill_rows}</tbody></table></section>"
        if skill_rows
        else ""
    )

    automation_rows = "".join(
        f"<tr><td>{escape(link.get('task_id', ''))}</td><td>{escape(link.get('matrix_workflow_id', ''))}</td><td>{escape(link.get('name', ''))}</td><td>{escape(link.get('platform', ''))}</td><td>{escape(str(link.get('confidence', '')))}</td></tr>"
        for link in automation_links or []
    )
    automation_table = (
        "<section class=\"panel\"><h3>Automation Matrix Suggestions</h3><table><thead><tr><th>Task</th><th>Matrix ID</th><th>Name</th><th>Platform</th><th>Confidence</th></tr></thead>"
        f"<tbody>{automation_rows}</tbody></table></section>"
        if automation_rows
        else ""
    )

    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <title>Workflow Synthesis Engine</title>
    <style>
        :root {{
            color-scheme: light dark;
            --bg: #0f172a;
            --panel: #1e2a44;
            --text: #e2e8f0;
            --accent: #38bdf8;
            --error: #f87171;
            --border: rgba(148, 163, 184, 0.3);
        }}
        body {{
            margin: 0;
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }}
        header {{
            padding: 2rem 3rem 1rem;
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(99, 102, 241, 0.15));
        }}
        header h1 {{
            margin-bottom: 0.4rem;
            font-size: 2rem;
        }}
        main {{
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
            gap: 1.5rem;
            padding: 1.5rem 3rem 3rem;
        }}
        form, section.panel {{
            background: var(--panel);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.45);
            border: 1px solid var(--border);
        }}
        textarea {{
            width: 100%;
            min-height: 220px;
            margin-top: 0.5rem;
            border-radius: 0.75rem;
            border: 1px solid var(--border);
            padding: 1rem;
            font-size: 0.95rem;
            background: rgba(15, 23, 42, 0.6);
            color: inherit;
            resize: vertical;
        }}
        select {{
            width: 100%;
            margin-top: 0.5rem;
            padding: 0.7rem;
            border-radius: 0.65rem;
            border: 1px solid var(--border);
            background: rgba(15, 23, 42, 0.6);
            color: inherit;
        }}
        button {{
            margin-top: 1.4rem;
            padding: 0.85rem 1.2rem;
            border-radius: 0.75rem;
            border: none;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            color: #0f172a;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 20px 35px -15px rgba(56, 189, 248, 0.6);
        }}
        pre {{
            background: rgba(15, 23, 42, 0.75);
            padding: 1rem;
            border-radius: 0.75rem;
            border: 1px solid var(--border);
            overflow: auto;
            max-height: 320px;
        }}
        .error {{
            background: rgba(248, 113, 113, 0.15);
            border: 1px solid rgba(248, 113, 113, 0.4);
            padding: 1rem;
            border-radius: 0.75rem;
            margin-top: 1rem;
            color: var(--error);
        }}
        .mermaid {{
            background: #fff;
            color: #000;
            padding: 1rem;
            border-radius: 0.75rem;
            border: 1px solid rgba(148, 163, 184, 0.4);
            margin-top: 1rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            font-size: 0.9rem;
        }}
        th, td {{
            padding: 0.6rem 0.8rem;
            border-bottom: 1px solid var(--border);
        }}
        tbody tr:hover {{
            background: rgba(148, 163, 184, 0.12);
        }}
    </style>
</head>
<body>
    <header>
        <h1>Workflow Synthesis Engine</h1>
        <p>Run the CESAR orchestrator with full enrichment, persistence, and automation recommendations.</p>
    </header>
    <main>
        <form method=\"post\" action=\"/run\">
            <label for=\"transcript\">Transcript</label>
            <textarea id=\"transcript\" name=\"transcript\" required>{transcript_value}</textarea>
            <label for=\"endpoint\">LLM Endpoint</label>
            <select id=\"endpoint\" name=\"endpoint\">
                <option value=\"\">Auto ({escape(selected_endpoint or '')})</option>
                {endpoint_options}
            </select>
            <button type=\"submit\">Run Orchestrator</button>
        </form>
        <section class=\"panel\">
            <h2>Workflow History</h2>
            {history_table}
        </section>
        <section class=\"panel\" style=\"grid-column: span 2;\">
            {error_html}
            {current_overview}
            {result_html}
            {mermaid_html}
            {skill_table}
            {automation_table}
        </section>
    </main>
</body>
</html>
"""

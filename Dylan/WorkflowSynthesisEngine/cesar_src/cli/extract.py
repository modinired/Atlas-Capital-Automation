
"""CLI entry point for running the Workflow Synthesis Engine end-to-end."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict

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
    """Minimal repository implementation retained for offline usage."""

    def __init__(self) -> None:
        self._storage: Dict[str, Dict[str, Any]] = {}

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
        self._storage[str(identifier)] = {
            "workflow_id": workflow_id,
            "workflow": workflow.model_dump(),
            "transcript": transcript,
            "mermaid": mermaid,
            "autogen_script_path": autogen_script_path,
            "skill_links": skill_links or [],
            "automation_links": automation_links or [],
        }
        return identifier


async def _run(config_path: Path, transcript_path: Path, endpoint: str | None) -> Dict[str, Any]:
    cfg = AppConfig.load(str(config_path))
    router = LLMRouter(cfg)

    repository = _build_repository(cfg)
    enricher = _build_enricher(cfg)
    automation_bridge = _build_automation_bridge(cfg)
    skill_matcher = _build_skill_matcher(cfg)
    automation_recommender = _build_automation_recommender(cfg)

    orchestrator = Orchestrator(
        router,
        repository,
        enricher=enricher,
        automation_bridge=automation_bridge,
        skill_matcher=skill_matcher,
        automation_recommender=automation_recommender,
    )

    transcript = transcript_path.read_text(encoding="utf-8")
    result = await orchestrator.process_transcript(transcript=transcript, endpoint=endpoint)
    return result


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Workflow Synthesis Engine")
    parser.add_argument("config", type=Path, help="Path to YAML config")
    parser.add_argument("transcript", type=Path, help="Path to transcript text file")
    parser.add_argument("--endpoint", type=str, default=None, help="Override LLM endpoint key")
    args = parser.parse_args()

    result = asyncio.run(_run(args.config, args.transcript, args.endpoint))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()

from __future__ import annotations

import uuid as _uuid
from typing import Protocol

from ..models.schemas import JobWorkflowSchema
from ..services.llm_router import LLMRouter
from .extractor_agent import ExtractorAgent
from .validator_agent import ValidatorAgent
from .visualizer_agent import VisualizerAgent


class WorkflowRepository(Protocol):
    """Protocol describing the persistence contract used by the orchestrator."""

    def record_workflow(
        self,
        *,
        workflow_id: str,
        workflow: JobWorkflowSchema,
        transcript: str,
        mermaid: str,
        autogen_script_path: str | None,
        skill_links: list[dict],
        automation_links: list[dict],
    ) -> int: ...


class Orchestrator:
    """Main entrypoint agent coordinating specialized droids (CESAR-SRC vision)."""

    def __init__(
        self,
        router: LLMRouter,
        repo: WorkflowRepository | None,
        *,
        telemetry: object | None = None,
        learnloop: object | None = None,
        enricher: object | None = None,
        automation_bridge: object | None = None,
        skill_matcher: object | None = None,
        automation_recommender: object | None = None,
    ) -> None:
        self.router = router
        self.repo = repo
        self.extractor = ExtractorAgent(router)
        self.validator = ValidatorAgent()
        self.visualizer = VisualizerAgent()
        self.telemetry = telemetry
        self.learnloop = learnloop
        self.enricher = enricher
        self.automation_bridge = automation_bridge
        self.skill_matcher = skill_matcher
        self.automation_recommender = automation_recommender

    async def process_transcript(self, *, transcript: str, endpoint: str | None = None) -> dict:
        extraction = await self.extractor.run({"transcript": transcript, "endpoint": endpoint})
        workflow: JobWorkflowSchema = extraction["workflow"]
        if self.telemetry:
            try:
                self.telemetry.log_interaction(
                    agent="extractor",
                    role="system",
                    inputs={"transcript_len": len(transcript)},
                    outputs=workflow.model_dump(),
                    meta={"endpoint": endpoint},
                )
            except Exception:
                pass
        await self.validator.run({"workflow": workflow})
        if self.telemetry:
            try:
                self.telemetry.log_interaction(
                    agent="validator",
                    role="system",
                    inputs={"task_count": len(workflow.tasks)},
                    outputs={"valid": True},
                    meta={},
                )
            except Exception:
                pass
        if self.enricher:
            try:
                workflow = self.enricher.enrich(workflow)
                await self.validator.run({"workflow": workflow})
            except Exception:
                pass
        rendering = await self.visualizer.run({"workflow": workflow})
        mermaid = rendering["mermaid"]
        if self.telemetry:
            try:
                self.telemetry.log_interaction(
                    agent="visualizer",
                    role="system",
                    inputs={"task_count": len(workflow.tasks)},
                    outputs={"mermaid_lines": len(mermaid.splitlines())},
                    meta={},
                )
            except Exception:
                pass

        autogen_script_path: str | None = None
        if self.automation_bridge:
            try:
                generated = self.automation_bridge.generate(workflow, transcript)
                autogen_script_path = str(generated) if generated else None
            except Exception:
                autogen_script_path = None

        skill_links: list[dict] = []
        if self.skill_matcher:
            try:
                skill_links = self.skill_matcher.match(workflow)
            except Exception:
                skill_links = []

        automation_links: list[dict] = []
        if self.automation_recommender:
            try:
                automation_links = self.automation_recommender.recommend(workflow)
            except Exception:
                automation_links = []

        run_identifier = f"wf-{_uuid.uuid4().hex}"
        workflow_identifier = self._persist_workflow(
            workflow_id=run_identifier,
            workflow=workflow,
            transcript=transcript,
            mermaid=mermaid,
            autogen_script_path=autogen_script_path,
            skill_links=skill_links,
            automation_links=automation_links,
        )

        if self.learnloop:
            try:
                import datetime as _dt

                payload_text = f"Workflow: {workflow.workflow_name}\nTasks: {len(workflow.tasks)}\n\nMermaid:\n{mermaid}"
                await self.learnloop.record_and_reflect(
                    doc_id=workflow_identifier,
                    title=workflow.workflow_name,
                    text=payload_text,
                    source="orchestrator",
                    created_at=_dt.datetime.utcnow().isoformat(),
                )
            except Exception:
                pass
        return {
            "workflow_id": workflow_identifier,
            "mermaid": mermaid,
            "task_count": len(workflow.tasks),
            "autogen_script_path": autogen_script_path,
            "skill_links": skill_links,
            "automation_links": automation_links,
        }

    def _persist_workflow(
        self,
        *,
        workflow_id: str,
        workflow: JobWorkflowSchema,
        transcript: str,
        mermaid: str,
        autogen_script_path: str | None,
        skill_links: list[dict],
        automation_links: list[dict],
    ) -> str:
        if not self.repo:
            return "workflow_unpersisted"
        try:
            self.repo.record_workflow(
                workflow_id=workflow_id,
                workflow=workflow,
                transcript=transcript,
                mermaid=mermaid,
                autogen_script_path=autogen_script_path,
                skill_links=skill_links,
                automation_links=automation_links,
            )
            return workflow_id
        except Exception:
            return "workflow_persist_error"

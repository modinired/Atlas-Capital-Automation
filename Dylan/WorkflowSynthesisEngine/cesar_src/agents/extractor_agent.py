"""Extractor agent that prompts an LLM to synthesize workflow schemas."""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from ..models.schemas import JobWorkflowSchema, TaskObject
from ..services.llm_router import LLMRouter, LLMRouterError
from .base import Agent

_EXTRACTOR_SYSTEM_PROMPT = (
    "You are the EJWCS Workflow Extractor agent. You analyze SME interview "
    "transcripts and must output a SINGLE JSON object matching the provided "
    "JSON Schema. Never include commentary, markdown, code fences, or any "
    "formatting besides raw JSON."
)


class ExtractorAgent(Agent):
    """LLM-backed agent that converts transcripts into workflow schemas."""

    name = "extractor"

    def __init__(self, router: LLMRouter) -> None:
        self._router = router

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript = payload["transcript"]
        endpoint = payload.get("endpoint")

        schema_json = json.dumps(JobWorkflowSchema.model_json_schema(), indent=2, sort_keys=True)
        user_prompt = (
            "Follow these steps:\n"
            "1. Read the transcript.\n"
            "2. Extract chronological tasks, dependencies, and conditional logic.\n"
            "3. Map roles, required skills, and knowledge where present.\n"
            "4. Any unknown field must be explicitly set to null (do not remove keys).\n"
            "5. Respond with raw JSON that validates against the schema.\n\n"
            f"JSON Schema reference (do NOT restate in output):\n{schema_json}\n\n"
            f"Transcript:\n{transcript}"
        )

        try:
            response = await self._router.chat(
                endpoint=endpoint,
                messages=[
                    {"role": "system", "content": _EXTRACTOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=4096,
            )
            workflow_obj = self._coerce_to_json(response)
            workflow = JobWorkflowSchema.model_validate(workflow_obj)
        except Exception as exc:  # noqa: BLE001 - fall back gracefully on any failure
            workflow = self._fallback(transcript, error=exc)
        return {"workflow": workflow}

    @staticmethod
    def _coerce_to_json(llm_output: str) -> Dict[str, Any]:
        """Parse the LLM response into a JSON-compatible dict."""
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            candidate = ExtractorAgent._extract_json_block(llm_output)
            return json.loads(candidate)

    @staticmethod
    def _extract_json_block(text: str) -> str:
        """Extract the first JSON object-like block from text for recovery."""
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("ExtractorAgent received non-JSON output from LLM")
        return match.group(0)

    @staticmethod
    def _fallback(transcript: str, error: Exception | None = None) -> JobWorkflowSchema:
        """Deterministic rule-based extraction when LLM access fails."""
        lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
        tasks: list[TaskObject] = []
        for idx, line in enumerate(lines, start=1):
            if ":" in line:
                speaker, content = line.split(":", 1)
                role = speaker.strip() or "Unknown"
                description = content.strip() or "Task description unavailable"
            else:
                role = "Unknown"
                description = line
            task_id = f"T{idx}"
            tasks.append(
                TaskObject(
                    task_id=task_id,
                    task_description=description,
                    role_owner=role,
                    precedes_tasks=[f"T{idx+1}"] if idx < len(lines) else [],
                )
            )
        if not tasks:
            tasks = [
                TaskObject(
                    task_id="T1",
                    task_description="No actionable steps detected",
                    role_owner="Unknown",
                )
            ]
        name_suffix = f" (fallback: {type(error).__name__})" if error else ""
        return JobWorkflowSchema(workflow_name=f"Fallback Workflow{name_suffix}", tasks=tasks)

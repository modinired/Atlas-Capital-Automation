"""Hands-free bridge between Workflow Synthesis Engine and Autogen workflow generator."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import sys

from ..models.schemas import JobWorkflowSchema


@dataclass(slots=True)
class AutogenWorkflowBridge:
    """Invokes the Gemini-powered Autogen workflow creator and returns script paths."""

    creator_script: Path
    workflows_dir: Path

    def __post_init__(self) -> None:
        self.creator_script = self.creator_script.resolve()
        self.workflows_dir = self.workflows_dir.resolve()
        if not self.creator_script.exists():
            raise FileNotFoundError(f"Autogen creator script not found at {self.creator_script}")
        if not self.workflows_dir.exists():
            self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, workflow: JobWorkflowSchema, transcript: str) -> Optional[Path]:
        """Generate an Autogen workflow script for the supplied workflow."""
        description = _build_description(workflow, transcript)
        target_name = _predict_filename(description)
        command = [
            sys.executable,
            str(self.creator_script),
            description,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                "Autogen workflow generation failed", result.stderr.strip() or result.stdout.strip()
            )
        candidate = self.workflows_dir / target_name
        if not candidate.exists():
            # creator may have applied additional normalisation; fall back to scanning directory
            scripts = sorted(self.workflows_dir.glob("workflow_*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
            candidate = scripts[0] if scripts else None
        return candidate


def _build_description(workflow: JobWorkflowSchema, transcript: str) -> str:
    lines = [
        f"Design an automation that executes the workflow '{workflow.workflow_name}'.",
        "The workflow tasks are ordered and include the following steps:",
    ]
    for task in workflow.tasks:
        lines.append(f"- {task.task_id}: {task.task_description} (owner: {task.role_owner})")
        if task.required_skill_tags:
            skills = ", ".join(item.description for item in task.required_skill_tags)
            lines.append(f"  Required automations/APIs: {skills}")
        if task.required_knowledge:
            knowledge = ", ".join(item.description for item in task.required_knowledge)
            lines.append(f"  Knowledge references: {knowledge}")
    lines.append("The original transcript summary is provided for additional context.")
    summary = transcript[:800].replace("\n", " ")
    lines.append(summary)
    return "\n".join(lines)


def _predict_filename(description: str) -> str:
    tokens = description.lower().split()
    sanitized = "".join(token if token.isalnum() else "_" for token in tokens)
    sanitized = sanitized[:50]
    return f"workflow_{sanitized}.py"

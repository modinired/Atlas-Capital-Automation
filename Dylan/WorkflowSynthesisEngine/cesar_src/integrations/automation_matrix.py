"""Automation Matrix Pack recommendations for CESAR workflows."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rapidfuzz import fuzz

from ..models.schemas import JobWorkflowSchema


@dataclass(slots=True)
class MatrixWorkflow:
    workflow_id: str
    name: str
    department: str
    role: str
    actions: str
    platform: str
    source_link: str
    kpis: str
    notes: str

    @property
    def searchable_text(self) -> str:
        return " ".join(
            filter(
                None,
                [self.name, self.actions, self.department, self.role, self.notes, self.kpis],
            )
        )


class AutomationMatrixRecommender:
    """Scores tasks against automation-matrix workflows for actionable suggestions."""

    def __init__(self, matrix_root: str | Path, *, min_score: int = 60, top_k: int = 3) -> None:
        root = Path(matrix_root).resolve()
        if not root.exists():
            raise ValueError(f"Automation matrix path not found: {root}")
        csv_path = root / "automation_matrix_workflows.csv"
        if not csv_path.exists():
            raise ValueError(f"automation_matrix_workflows.csv missing in {root}")
        self.matrix: list[MatrixWorkflow] = self._load(csv_path)
        self.min_score = min_score
        self.top_k = top_k

    def recommend(self, workflow: JobWorkflowSchema) -> list[dict]:
        suggestions: list[dict] = []
        for task in workflow.tasks:
            scored = self._score_task(task.task_description)
            for score, wf in scored:
                suggestions.append(
                    {
                        "task_id": task.task_id,
                        "matrix_workflow_id": wf.workflow_id,
                        "name": wf.name,
                        "platform": wf.platform,
                        "actions": wf.actions,
                        "department": wf.department,
                        "role": wf.role,
                        "kpis": wf.kpis,
                        "source_link": wf.source_link,
                        "confidence": round(score / 100.0, 3),
                    }
                )
        return suggestions

    def _score_task(self, description: str) -> list[tuple[int, MatrixWorkflow]]:
        scored: list[tuple[int, MatrixWorkflow]] = []
        for workflow in self.matrix:
            score = fuzz.token_set_ratio(description, workflow.searchable_text)
            if score >= self.min_score:
                scored.append((score, workflow))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[: self.top_k]

    @staticmethod
    def _load(csv_path: Path) -> list[MatrixWorkflow]:
        with csv_path.open(encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            return [
                MatrixWorkflow(
                    workflow_id=row.get("WorkflowID", "").strip(),
                    name=row.get("Name", "").strip(),
                    department=row.get("Department", "").strip(),
                    role=row.get("Role", "").strip(),
                    actions=row.get("Actions", "").strip(),
                    platform=row.get("Platform", "").strip(),
                    source_link=row.get("SourceLink", "").strip(),
                    kpis=row.get("KPIs", "").strip(),
                    notes=row.get("Notes", "").strip(),
                )
                for row in reader
                if row.get("WorkflowID")
            ]

    def platforms(self) -> Iterable[str]:
        return sorted({wf.platform for wf in self.matrix if wf.platform})

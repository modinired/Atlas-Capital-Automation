"""Skill node matcher leveraging the Mr. Mayhem registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from rapidfuzz import fuzz

from ..models.schemas import JobWorkflowSchema


@dataclass(slots=True)
class SkillNode:
    skill_id: str
    display_name: str
    namespace: str
    tags: str
    source: Path

    @property
    def searchable_text(self) -> str:
        return f"{self.display_name} {self.tags} {self.namespace}"


class SkillNodeMatcher:
    """Matches workflow tasks to skill nodes using rapid token-set similarity."""

    def __init__(self, registry_root: str | Path, *, min_score: int = 68, top_k: int = 3) -> None:
        root = Path(registry_root).resolve()
        if not root.exists():
            raise ValueError(f"Skill node registry not found: {root}")
        self._skills: list[SkillNode] = []
        self.min_score = min_score
        self.top_k = top_k
        self._load_registry(root)

    def match(self, workflow: JobWorkflowSchema) -> list[dict]:
        matches: list[dict] = []
        for task in workflow.tasks:
            candidates = self._score_task(task.task_description)
            for score, skill in candidates:
                matches.append(
                    {
                        "task_id": task.task_id,
                        "skill_id": skill.skill_id,
                        "skill_name": skill.display_name,
                        "namespace": skill.namespace,
                        "confidence": round(score / 100.0, 3),
                        "source": str(skill.source),
                    }
                )
        return matches

    def _score_task(self, description: str) -> list[tuple[int, SkillNode]]:
        scored: list[tuple[int, SkillNode]] = []
        for skill in self._skills:
            score = fuzz.token_set_ratio(description, skill.searchable_text)
            if score >= self.min_score:
                scored.append((score, skill))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[: self.top_k]

    def _load_registry(self, root: Path) -> None:
        for path in sorted(root.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for entry in data.get("skills", []):
                skill_id = entry.get("id", "").strip()
                if not skill_id:
                    continue
                display = entry.get("display_name", skill_id).replace("_", " ")
                tags = " ".join(entry.get("tags", []))
                namespace = ".".join(skill_id.split(".")[:-1]) or "general"
                self._skills.append(
                    SkillNode(
                        skill_id=skill_id,
                        display_name=display,
                        namespace=namespace,
                        tags=tags,
                        source=path,
                    )
                )

    @property
    def total_skills(self) -> int:
        return len(self._skills)

    def namespaces(self) -> Iterable[str]:
        return sorted({skill.namespace for skill in self._skills})

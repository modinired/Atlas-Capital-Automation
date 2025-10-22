"""Utility layer providing enrichment from the Master Job Tree system."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from rapidfuzz import fuzz, process

from ..models.schemas import JobWorkflowSchema, KnowledgeItem, SkillItem


class MasterJobTreeEnricher:
    """Augments workflow tasks using the Master Job Tree deliverables."""

    def __init__(self, project_root: str | Path, *, api_catalog_path: str | None = None) -> None:
        root = Path(project_root).resolve()
        if not root.exists():
            raise ValueError(f"Master Job Tree root not found: {root}")
        self._api_catalog = _load_api_catalog(api_catalog_path or root / "config" / "apis.csv")

    def enrich(self, workflow: JobWorkflowSchema) -> JobWorkflowSchema:
        """Inject API recommendations and knowledge hints into each task."""
        for task in workflow.tasks:
            recommendations = self._recommend_apis(task.task_description)
            if recommendations:
                task.required_skill_tags.extend(
                    SkillItem(id=item["name"], description=item["endpoint"]) for item in recommendations
                )
            knowledge = self._recommend_knowledge(task.task_description)
            if knowledge:
                task.required_knowledge.extend(
                    KnowledgeItem(id=ref["id"], description=ref["description"]) for ref in knowledge
                )
        return workflow

    def _recommend_apis(self, text: str) -> list[dict]:
        choices = [entry["keywords"] for entry in self._api_catalog]
        mapping = {entry["keywords"]: entry for entry in self._api_catalog}
        results = process.extract(text, choices, scorer=fuzz.token_set_ratio, limit=5)
        suggestions = []
        for match, score, _ in results:
            if score < 65:
                continue
            entry = mapping[match]
            suggestions.append(entry)
            if len(suggestions) >= 3:
                break
        return suggestions

    def _recommend_knowledge(self, text: str) -> list[dict]:
        knowledge_base = _load_canonical_knowledge()
        results = process.extract(text, [item["keywords"] for item in knowledge_base], scorer=fuzz.token_set_ratio, limit=5)
        enriched: list[dict] = []
        for match, score, _ in results:
            if score < 70:
                continue
            item = next(entry for entry in knowledge_base if entry["keywords"] == match)
            enriched.append(item)
            if len(enriched) >= 2:
                break
        return enriched


@lru_cache(maxsize=1)
def _load_api_catalog(path: str | Path) -> list[dict]:
    catalog_path = Path(path)
    if not catalog_path.exists():
        raise ValueError(f"Master Job Tree API catalog missing: {catalog_path}")
    entries: list[dict] = []
    with catalog_path.open("r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            keywords = row.get("Keywords", "").lower()
            entries.append(
                {
                    "name": row.get("API Name", "").strip(),
                    "endpoint": row.get("Endpoint", "").strip(),
                    "keywords": keywords,
                    "description": row.get("Description", "").strip(),
                }
            )
    return entries


@lru_cache(maxsize=1)
def _load_canonical_knowledge() -> list[dict]:
    """Return curated occupational knowledge references for enrichment."""
    sources: Iterable[dict[str, str]] = (
        {"id": "APQC-PCF", "description": "APQC Process Classification Framework best practices", "keywords": "process framework operations quality"},
        {"id": "ONET-TASK-ANALYSIS", "description": "O*NET occupational task guidelines", "keywords": "occupation task standard"},
        {"id": "ISO-9001", "description": "ISO 9001 quality management requirements", "keywords": "quality management iso compliance"},
        {"id": "NIST-CSF", "description": "NIST Cybersecurity Framework references", "keywords": "cybersecurity incident response nist"},
    )
    return list(sources)

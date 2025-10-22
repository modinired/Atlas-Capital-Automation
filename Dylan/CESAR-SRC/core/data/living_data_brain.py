"""Living Data Brain repository access for CESAR-SRC.

Provides a strongly-typed interface for reading and writing telemetry data to the
Living Data Brain SQLite database that powers the shared CESAR/Jerry analytics
stack. All timestamps are handled in UTC and converted to timezone-aware values
before persistence to maintain consistency with the upstream schema.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import structlog
from sqlalchemy import MetaData, Table, create_engine, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, NoSuchTableError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

logger = structlog.get_logger(__name__)


DEFAULT_DB_PATH = Path.home() / "living_data_brain.db"


def _resolve_db_path(db_path: Optional[Path | str] = None) -> Path:
    """Resolve the SQLite database path using env overrides and validation."""
    candidates: Iterable[Optional[Path]] = (
        Path(str(db_path)).expanduser() if db_path else None,
        Path(os.getenv("LIVING_DATA_BRAIN_DB_PATH", "")).expanduser()
        if os.getenv("LIVING_DATA_BRAIN_DB_PATH")
        else None,
        DEFAULT_DB_PATH,
    )

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    # Fall back to explicit candidate if provided even when missing so callers
    # receive a precise error message.
    if db_path:
        return Path(str(db_path)).expanduser()

    if env_path := os.getenv("LIVING_DATA_BRAIN_DB_PATH"):
        return Path(env_path).expanduser()

    return DEFAULT_DB_PATH


@dataclass(frozen=True)
class AgentRunRecord:
    """Structured payload for logging agent executions."""

    agent_name: str
    started_at: datetime
    duration_ms: float
    confidence: Optional[float]
    cost_usd: Optional[float]
    tokens_used: Optional[int]
    status: str
    trace_id: Optional[str]
    output_payload: Dict[str, Any]
    metadata: Dict[str, Any]

    def as_db_payload(self) -> Dict[str, Any]:
        """Convert to database column mapping respecting schema expectations."""
        run_ts = self.started_at.astimezone(timezone.utc)

        def _to_serializable(value: Any) -> Any:
            try:
                json.dumps(value)
                return value
            except TypeError:
                if isinstance(value, datetime):
                    return value.astimezone(timezone.utc).isoformat()
                if isinstance(value, set):
                    return sorted(_to_serializable(v) for v in value)
                if hasattr(value, "dict"):
                    return _to_serializable(value.__dict__)
                return str(value)

        output_payload = _to_serializable(self.output_payload)
        meta_payload = {
            **{k: _to_serializable(v) for k, v in self.metadata.items()},
            "status": self.status,
            "trace_id": self.trace_id,
        }

        payload = {
            "script_name": self.agent_name,
            "run_ts": run_ts,
            "execution_time_ms": int(round(self.duration_ms)),
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "confidence_score": self.confidence,
            "learning_reward": None,
            "output_payload": output_payload,
            "meta": meta_payload,
        }
        return payload


class LivingDataBrainRepository:
    """SQLAlchemy-backed repository for the Living Data Brain SQLite database."""

    REQUIRED_TABLES = {
        "runs",
        "dashboard_kpis",
        "dashboard_visualizations",
        "workflow_automations",
        "workflow_automation_logs",
        "governance_resources",
        "automation_registry",
        "skill_nodes",
    }

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = _resolve_db_path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Living Data Brain database not found at {self.db_path}. "
                "Run living_data_brain.py to generate seed data or set "
                "LIVING_DATA_BRAIN_DB_PATH to an existing database."
            )

        self.engine: Engine = create_engine(
            f"sqlite:///{self.db_path}", future=True, echo=False
        )
        self._ensure_continuity_tables()

        self._metadata = MetaData()
        self._metadata.reflect(bind=self.engine, only=self.REQUIRED_TABLES)

        self._runs: Table = self._metadata.tables["runs"]
        self._automations: Table = self._metadata.tables["workflow_automations"]
        self._automation_logs: Table = self._metadata.tables[
            "workflow_automation_logs"
        ]
        self._governance_resources: Table = self._metadata.tables[
            "governance_resources"
        ]
        self._automation_registry: Table = self._metadata.tables[
            "automation_registry"
        ]
        self._skill_nodes: Table = self._metadata.tables["skill_nodes"]

        self._SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)

        logger.info(
            "living_data_brain_repository_initialized",
            db_path=str(self.db_path),
            tables=list(self._metadata.tables.keys()),
        )

    @contextmanager
    def session_scope(self) -> Iterable[Session]:
        """Context manager that provides a transactional session."""
        session: Session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Agent runs
    # ------------------------------------------------------------------
    def log_agent_run(self, record: AgentRunRecord) -> None:
        """Persist a new agent execution record into the `runs` table."""
        payload = record.as_db_payload()
        try:
            with self.engine.begin() as conn:
                conn.execute(insert(self._runs), payload)
        except SQLAlchemyError as exc:
            logger.warning(
                "living_data_brain_run_log_failed",
                error=str(exc),
                agent=record.agent_name,
                trace_id=record.trace_id,
            )

    def fetch_recent_runs(self, limit: int = 25) -> list[Dict[str, Any]]:
        """Retrieve the most recent runs for diagnostics and analytics."""
        stmt = select(self._runs).order_by(self._runs.c.run_ts.desc()).limit(limit)
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            rows = [dict(row._mapping) for row in result]
        return rows

    # ------------------------------------------------------------------
    # Governance & knowledge resources
    # ------------------------------------------------------------------
    def register_governance_resource(
        self,
        name: str,
        resource_type: str,
        file_path: str,
        sha256: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload = {
            "name": name,
            "resource_type": resource_type,
            "file_path": file_path,
            "sha256": sha256,
            "source": source,
            "metadata_json": metadata or {},
        }
        self._upsert(self._governance_resources, payload, "file_path")

    # ------------------------------------------------------------------
    # Automation registry & skills
    # ------------------------------------------------------------------
    def register_automation_entry(self, entry: Dict[str, Any]) -> None:
        payload = {
            "identifier": entry["identifier"],
            "name": entry["name"],
            "category": entry.get("category"),
            "endpoint": entry.get("endpoint"),
            "auth": entry.get("auth"),
            "quality_score": entry.get("quality_score"),
            "metadata_json": entry.get("metadata", {}),
        }
        self._upsert(self._automation_registry, payload, "identifier")

    def register_skill_node(self, node: Dict[str, Any]) -> None:
        payload = {
            "node_id": node["node_id"],
            "display_name": node["display_name"],
            "department": node.get("department"),
            "version": node.get("version"),
            "status": node.get("status"),
            "metadata_json": node.get("metadata", {}),
        }
        self._upsert(self._skill_nodes, payload, "node_id")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _upsert(self, table: Table, payload: Dict[str, Any], unique_field: str) -> None:
        stmt = sqlite_insert(table).values(**payload)
        update_values = {key: stmt.excluded[key] for key in payload.keys() if key != unique_field}
        stmt = stmt.on_conflict_do_update(index_elements=[table.c[unique_field]], set_=update_values)
        try:
            with self.engine.begin() as conn:
                conn.execute(stmt)
        except SQLAlchemyError as exc:
            logger.warning("living_data_brain_upsert_failed", table=table.name, error=str(exc))

    def _ensure_continuity_tables(self) -> None:
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS governance_resources (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                sha256 TEXT NOT NULL,
                source TEXT,
                metadata_json JSON,
                created_ts TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS automation_registry (
                id INTEGER PRIMARY KEY,
                identifier TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT,
                endpoint TEXT,
                auth TEXT,
                quality_score REAL,
                metadata_json JSON,
                created_ts TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS skill_nodes (
                id INTEGER PRIMARY KEY,
                node_id TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                department TEXT,
                version TEXT,
                status TEXT,
                metadata_json JSON,
                created_ts TIMESTAMP
            )
            """,
        ]

        with self.engine.begin() as conn:
            for ddl in ddl_statements:
                conn.exec_driver_sql(ddl)

    # ------------------------------------------------------------------
    # Workflow automations
    # ------------------------------------------------------------------
    def _normalize_datetime(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def ensure_workflow_automation(
        self,
        name: str,
        objective: Optional[str] = None,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        last_reviewed: Optional[datetime] = None,
    ) -> int:
        """Ensure a workflow automation row exists and return its primary key."""
        normalized_last_reviewed = self._normalize_datetime(last_reviewed)

        with self.engine.begin() as conn:
            existing = conn.execute(
                select(self._automations.c.id).where(self._automations.c.name == name)
            ).scalar_one_or_none()

            now_utc = datetime.now(timezone.utc)
            if existing is None:
                result = conn.execute(
                    insert(self._automations).values(
                        name=name,
                        objective=objective,
                        status=status or "draft",
                        owner=owner,
                        last_reviewed=normalized_last_reviewed or now_utc,
                        created_ts=now_utc,
                    )
                )
                automation_id = result.inserted_primary_key[0]
            else:
                update_payload: Dict[str, Any] = {}
                if objective is not None:
                    update_payload["objective"] = objective
                if status is not None:
                    update_payload["status"] = status
                if owner is not None:
                    update_payload["owner"] = owner
                update_payload["last_reviewed"] = normalized_last_reviewed or now_utc

                if update_payload:
                    conn.execute(
                        update(self._automations)
                        .where(self._automations.c.id == existing)
                        .values(**update_payload)
                    )
                automation_id = existing

        return int(automation_id)

    def log_automation_review(
        self,
        automation_name: str,
        summary: str,
        source: str = "manual",
        objective: Optional[str] = None,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        review_timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append an automation review entry and refresh the automation record."""
        automation_id = self.ensure_workflow_automation(
            name=automation_name,
            objective=objective,
            status=status,
            owner=owner,
            last_reviewed=review_timestamp,
        )

        enriched_summary = summary
        if metadata:
            safe_metadata = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
            enriched_summary = f"{summary}\n\nmetadata: {safe_metadata}"

        log_payload = {
            "automation_id": automation_id,
            "summary": enriched_summary,
            "source": source,
            "created_ts": self._normalize_datetime(review_timestamp) or datetime.now(timezone.utc),
        }

        try:
            with self.engine.begin() as conn:
                conn.execute(insert(self._automation_logs), log_payload)
        except SQLAlchemyError as exc:
            logger.warning(
                "living_data_brain_automation_log_failed",
                error=str(exc),
                automation=automation_name,
            )

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def try_create(cls, db_path: Optional[Path | str] = None) -> Optional["LivingDataBrainRepository"]:
        """Create a repository if the database is available; otherwise return None."""
        try:
            return cls(db_path=db_path)
        except FileNotFoundError:
            logger.debug("living_data_brain_db_missing", db_path=str(_resolve_db_path(db_path)))
            return None
        except Exception:
            logger.exception("living_data_brain_repo_init_failed")
            return None


_repository_singleton: Optional[LivingDataBrainRepository] = None


def get_repository() -> Optional[LivingDataBrainRepository]:
    """Singleton accessor used throughout the CESAR codebase."""
    global _repository_singleton
    if _repository_singleton is None:
        _repository_singleton = LivingDataBrainRepository.try_create()
    return _repository_singleton


__all__ = [
    "AgentRunRecord",
    "LivingDataBrainRepository",
    "get_repository",
]

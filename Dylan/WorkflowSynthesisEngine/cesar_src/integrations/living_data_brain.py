
"""Reliable persistence adapter for the Living Data Brain analytics store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, selectinload, sessionmaker

from ..models.schemas import JobWorkflowSchema, TaskObject


class _Base(DeclarativeBase):
    """Shared declarative base for Living Data Brain integration tables."""


class WorkflowRunRecord(_Base):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    workflow_name: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    mermaid: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    autogen_script_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    tasks: Mapped[list[WorkflowTaskRecord]] = relationship(
        "WorkflowTaskRecord",
        cascade="all, delete-orphan",
        back_populates="workflow_run",
        lazy="selectin",
    )
    skills: Mapped[list[WorkflowSkillLink]] = relationship(
        "WorkflowSkillLink",
        cascade="all, delete-orphan",
        back_populates="workflow_run",
        lazy="selectin",
    )
    automations: Mapped[list[WorkflowAutomationLink]] = relationship(
        "WorkflowAutomationLink",
        cascade="all, delete-orphan",
        back_populates="workflow_run",
        lazy="selectin",
    )


class WorkflowTaskRecord(_Base):
    __tablename__ = "workflow_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role_owner: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    workflow_run: Mapped[WorkflowRunRecord] = relationship("WorkflowRunRecord", back_populates="tasks")


class WorkflowSkillLink(_Base):
    __tablename__ = "workflow_skill_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(256), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(256), nullable=False)
    namespace: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str | None] = mapped_column(String(512), nullable=True)

    workflow_run: Mapped[WorkflowRunRecord] = relationship("WorkflowRunRecord", back_populates="skills")


class WorkflowAutomationLink(_Base):
    __tablename__ = "workflow_automation_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False)
    matrix_workflow_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    kpis: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    workflow_run: Mapped[WorkflowRunRecord] = relationship("WorkflowRunRecord", back_populates="automations")


class LivingDataBrainRepository:
    """Writes validated workflows into the Living Data Brain SQLite store."""

    def __init__(self, database_path: str | Path) -> None:
        db_path = Path(database_path)
        if not db_path.parent.exists():
            raise ValueError(f"Living Data Brain directory does not exist: {db_path.parent}")
        self._engine = create_engine(f"sqlite:///{db_path}", future=True)
        _Base.metadata.create_all(self._engine, checkfirst=True)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine, expire_on_commit=False, future=True)

    def record_workflow(
        self,
        *,
        workflow_id: str,
        workflow: JobWorkflowSchema,
        transcript: str,
        mermaid: str,
        autogen_script_path: str | None,
        skill_links: list[dict] | None,
        automation_links: list[dict] | None,
    ) -> int:
        """Persist a workflow, tasks, and enrichment artefacts."""
        payload = workflow.model_dump(mode="json")
        with self._session_factory() as session:
            record = WorkflowRunRecord(
                workflow_id=workflow_id,
                workflow_name=workflow.workflow_name,
                transcript=transcript,
                mermaid=mermaid,
                payload=payload,
                autogen_script_path=autogen_script_path,
            )
            session.add(record)
            session.flush()
            session.refresh(record)

            session.add_all(
                [
                    WorkflowTaskRecord(
                        workflow_run_id=record.id,
                        task_id=task.task_id,
                        role_owner=task.role_owner,
                        description=task.task_description,
                        task_metadata=_serialize_task_metadata(task),
                    )
                    for task in workflow.tasks
                ]
            )

            if skill_links:
                session.add_all(
                    [
                        WorkflowSkillLink(
                            workflow_run_id=record.id,
                            task_id=link["task_id"],
                            skill_id=link["skill_id"],
                            skill_name=link["skill_name"],
                            namespace=link["namespace"],
                            confidence=float(link.get("confidence", 0.0)),
                            source=link.get("source"),
                        )
                        for link in skill_links
                    ]
                )

            if automation_links:
                session.add_all(
                    [
                        WorkflowAutomationLink(
                            workflow_run_id=record.id,
                            task_id=link["task_id"],
                            matrix_workflow_id=link["matrix_workflow_id"],
                            name=link["name"],
                            platform=link.get("platform"),
                            actions=link.get("actions"),
                            department=link.get("department"),
                            role=link.get("role"),
                            kpis=link.get("kpis"),
                            source_link=link.get("source_link"),
                            confidence=float(link.get("confidence", 0.0)),
                        )
                        for link in automation_links
                    ]
                )

            session.commit()
            return record.id

    def fetch_recent_runs(self, limit: int = 25) -> list[dict]:
        """Return the most recent workflow runs with task counts."""
        with self._session_factory() as session:
            query = (
                session.query(WorkflowRunRecord)
                .order_by(WorkflowRunRecord.created_at.desc())
                .limit(limit)
                .options(selectinload(WorkflowRunRecord.tasks))
            )
            return [
                {
                    "workflow_id": item.workflow_id,
                    "workflow_name": item.workflow_name,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "task_count": len(item.tasks),
                    "autogen_script_path": item.autogen_script_path,
                }
                for item in query
            ]

    def get(self, workflow_id: str) -> Optional[dict]:
        with self._session_factory() as session:
            record = (
                session.query(WorkflowRunRecord)
                .filter(WorkflowRunRecord.workflow_id == workflow_id)
                .options(
                    selectinload(WorkflowRunRecord.tasks),
                    selectinload(WorkflowRunRecord.skills),
                    selectinload(WorkflowRunRecord.automations),
                )
                .one_or_none()
            )
            if not record:
                return None
            return {
                "workflow_id": record.workflow_id,
                "workflow_name": record.workflow_name,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "transcript": record.transcript,
                "mermaid": record.mermaid,
                "payload": record.payload,
                "autogen_script_path": record.autogen_script_path,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "role_owner": task.role_owner,
                        "description": task.description,
                        "metadata": task.task_metadata,
                    }
                    for task in record.tasks
                ],
                "skills": [
                    {
                        "task_id": skill.task_id,
                        "skill_id": skill.skill_id,
                        "skill_name": skill.skill_name,
                        "namespace": skill.namespace,
                        "confidence": skill.confidence,
                        "source": skill.source,
                    }
                    for skill in record.skills
                ],
                "automations": [
                    {
                        "task_id": auto.task_id,
                        "matrix_workflow_id": auto.matrix_workflow_id,
                        "name": auto.name,
                        "platform": auto.platform,
                        "actions": auto.actions,
                        "department": auto.department,
                        "role": auto.role,
                        "kpis": auto.kpis,
                        "source_link": auto.source_link,
                        "confidence": auto.confidence,
                    }
                    for auto in record.automations
                ],
            }


def _serialize_task_metadata(task: TaskObject) -> dict:
    record: dict[str, Iterable[dict[str, str]] | str | list[str]] = {}
    if task.precedes_tasks:
        record["precedes_tasks"] = list(task.precedes_tasks)
    if task.dependencies:
        record["dependencies"] = list(task.dependencies)
    if task.conditional_logic:
        record["conditional_logic"] = json.loads(task.conditional_logic.model_dump_json())
    if task.required_knowledge:
        record["required_knowledge"] = [item.model_dump() for item in task.required_knowledge]
    if task.required_skill_tags:
        record["required_skill_tags"] = [item.model_dump() for item in task.required_skill_tags]
    return record

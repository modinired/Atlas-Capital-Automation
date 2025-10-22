"""Persistence abstractions used by orchestration and tests."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session, sessionmaker

from .db import WorkflowModel


class RepositoryProtocol(Protocol):
    def save(self, workflow_name: str, workflow, mermaid_code: str) -> str: ...
    def get(self, workflow_id: str) -> WorkflowModel | None: ...


class WorkflowRepository:
    """Stores workflows in the SQLAlchemy-backed database."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, workflow_name: str, workflow, mermaid_code: str) -> str:
        with self._session_factory() as session:
            model = WorkflowModel(name=workflow_name, json_data=workflow.model_dump(), mermaid=mermaid_code)
            session.add(model)
            session.commit()
            return model.id

    def get(self, workflow_id: str) -> WorkflowModel | None:
        with self._session_factory() as session:
            return session.get(WorkflowModel, workflow_id)

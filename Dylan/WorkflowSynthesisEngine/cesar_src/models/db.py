"""Lightweight SQLAlchemy models used by the test suite."""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for simple workflow persistence."""


class WorkflowModel(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    json_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    mermaid: Mapped[str] = mapped_column(Text, nullable=False)


def make_session(database_url: str) -> sessionmaker[Session]:
    """Return a session factory and ensure schema is created."""
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


"""
Unified Database Schema for the Workflow Synthesis Engine.

This module defines the complete SQLAlchemy ORM data model for the system,
synthesizing schemas from CESAR-SRC, Workflow Knowledge Suite, and the
Automation Matrix Pack. It uses PostgreSQL as the backend and leverages
pgvector for embedding storage and retrieval.

The schema is designed to be the single source of truth for:
- Roles and Agents: Who performs the work.
- Skill Nodes: The atomic, reusable capabilities of the system.
- Workflows: Compositions of skill nodes to achieve a goal.
- Execution Logs: Records of every workflow run and step.
- Knowledge & Reflection: The learning and improvement loop.
- Asset Management: Ingestion and tracking of scraped or submitted assets.
"""

from __future__ import annotations

import datetime
import uuid
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from pgvector.sqlalchemy import Vector


# --- Base Configuration ---

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

# --- Core Models based on Workflow Knowledge Suite ---

class Role(Base):
    __tablename__ = "roles"
    role_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_title: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    role_type: Mapped[str] = mapped_column(String(16), nullable=False, default="human")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    skills: Mapped[List["RoleSkillMap"]] = relationship(back_populates="role")
    owned_skills: Mapped[List["SkillNode"]] = relationship(back_populates="owner")
    owned_workflows: Mapped[List["Workflow"]] = relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"<Role(role_id='{self.role_id}', title='{self.role_title}')>"

class SkillNode(Base):
    __tablename__ = "skill_nodes"
    skill_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_role_id: Mapped[str] = mapped_column(String(32), ForeignKey("roles.role_id"), nullable=False)
    
    # The "contract" for the skill, making it composable
    input_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # How to execute this skill
    runtime_binding: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner: Mapped["Role"] = relationship(back_populates="owned_skills")
    roles: Mapped[List["RoleSkillMap"]] = relationship(back_populates="skill")

    __table_args__ = (UniqueConstraint("skill_name", "version", name="ux_skill_name_version"),)

    def __repr__(self) -> str:
        return f"<SkillNode(skill_id='{self.skill_id}', name='{self.skill_name}', version='{self.version}')>"

class RoleSkillMap(Base):
    __tablename__ = "role_skill_map"
    role_id: Mapped[str] = mapped_column(String(32), ForeignKey("roles.role_id"), primary_key=True)
    skill_id: Mapped[str] = mapped_column(String(32), ForeignKey("skill_nodes.skill_id"), primary_key=True)
    permission: Mapped[str] = mapped_column(String(16), nullable=False, default="use")

    role: Mapped["Role"] = relationship(back_populates="skills")
    skill: Mapped["SkillNode"] = relationship(back_populates="roles")

class Workflow(Base):
    __tablename__ = "workflows"
    workflow_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_name: Mapped[str] = mapped_column(String(128), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    version: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_role_id: Mapped[str] = mapped_column(String(32), ForeignKey("roles.role_id"), nullable=False)
    
    # The "genome" defines the graph of skill nodes and their connections
    genome: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner: Mapped["Role"] = relationship(back_populates="owned_workflows")
    steps: Mapped[List["WorkflowStep"]] = relationship(back_populates="workflow")
    apis: Mapped[List["WorkflowApiMap"]] = relationship(back_populates="workflow")

    __table_args__ = (UniqueConstraint("workflow_name", "version", name="ux_workflow_name_version"),)

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    step_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(32), ForeignKey("workflows.workflow_id"), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(32), ForeignKey("skill_nodes.skill_id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Parameters specific to this instance of the skill in the workflow
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Logic for branching to the next step
    next_step_logic: Mapped[dict] = mapped_column(JSONB, nullable=False)

    workflow: Mapped["Workflow"] = relationship(back_populates="steps")
    skill: Mapped["SkillNode"] = relationship()

# --- Models from Automation Matrix Pack ---

class Api(Base):
    __tablename__ = "apis"
    name: Mapped[str] = mapped_column(String(128), primary_key=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    base_url: Mapped[Optional[str]] = mapped_column(Text)
    docs_url: Mapped[Optional[str]] = mapped_column(Text)
    credentials_template: Mapped[Optional[dict]] = mapped_column(JSONB)

    workflows: Mapped[List["WorkflowApiMap"]] = relationship(back_populates="api")

class WorkflowApiMap(Base):
    __tablename__ = "workflow_api_map"
    workflow_id: Mapped[str] = mapped_column(String(32), ForeignKey("workflows.workflow_id"), primary_key=True)
    api_name: Mapped[str] = mapped_column(String(128), ForeignKey("apis.name"), primary_key=True)
    purpose: Mapped[Optional[str]] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)

    workflow: Mapped["Workflow"] = relationship(back_populates="apis")
    api: Mapped["Api"] = relationship(back_populates="workflows")

class StagedAsset(Base):
    __tablename__ = "staged_assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text)
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="pending_review", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class WorkflowSuggestion(Base):
    __tablename__ = "workflow_suggestions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(32), ForeignKey("workflows.workflow_id"), nullable=False)
    suggestion_type: Mapped[str] = mapped_column(String(64), nullable=False)
    suggestion_details: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

# --- Models from Manus.im Clone (for user interaction) ---

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, default="New Conversation")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False) # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

# --- Engine and Session Factory ---

def create_db_engine_and_session(database_url: str):
    """
    Creates the SQLAlchemy engine and session factory.
    
    Args:
        database_url: The PostgreSQL connection string.
        
    Returns:
        A tuple of (engine, SessionLocal).
    """
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

def create_all_tables(engine):
    """
    Creates all tables in the database defined in this model.
    """
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Example usage:
    # This block can be used to initialize the database from the command line.
    # Remember to set the DATABASE_URL environment variable.
    import os
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set.")
        print("Example: export DATABASE_URL='postgresql://user:password@localhost/dbname'")
    else:
        print(f"Initializing database at {db_url}...")
        engine, _ = create_db_engine_and_session(db_url)
        create_all_tables(engine)
        print("Database initialization complete.")



"""
Repository for the Unified Workflow Synthesis Engine Database.

This module provides a high-level, abstracted interface for all database
operations. It encapsulates SQLAlchemy session management and provides a clean,
use-case-oriented API for services to interact with the database models.

This repository pattern ensures that the business logic is decoupled from the
data access logic, making the system more maintainable, testable, and scalable.
"""

from __future__ import annotations

import contextlib
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.orm import Session, sessionmaker

from . import models


class UnifiedRepository:
    """Provides a single, unified interface for all database operations."""

    def __init__(self, session_factory: sessionmaker[Session]):
        """
        Initializes the repository with a session factory.

        Args:
            session_factory: A configured SQLAlchemy sessionmaker.
        """
        self._session_factory = session_factory

    @contextlib.contextmanager
    def session_scope(self) -> Session:
        """Provide a transactional scope around a series of operations."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # --- Skill Node Operations ---

    def create_skill_node(self, skill_data: Dict[str, Any]) -> models.SkillNode:
        """Creates a new skill node in the database."""
        with self.session_scope() as session:
            # Ensure owner_role exists or handle appropriately
            owner_role_id = skill_data.get("owner_role_id")
            if not session.get(models.Role, owner_role_id):
                # In a real system, you might create a default role or raise a specific error
                # For now, we assume the role exists.
                pass

            new_skill = models.SkillNode(**skill_data)
            session.add(new_skill)
            session.flush()  # Flush to get the generated skill_id
            session.refresh(new_skill)
            return new_skill

    def get_skill_node_by_name(self, name: str, version: str) -> Optional[models.SkillNode]:
        """Retrieves a skill node by its unique name and version."""
        with self.session_scope() as session:
            return session.query(models.SkillNode).filter_by(skill_name=name, version=version).one_or_none()

    # --- Workflow Operations ---

    def create_workflow(self, workflow_data: Dict[str, Any]) -> models.Workflow:
        """Creates a new workflow in the database."""
        with self.session_scope() as session:
            new_workflow = models.Workflow(**workflow_data)
            session.add(new_workflow)
            session.flush()
            session.refresh(new_workflow)
            return new_workflow

    def get_workflow_by_id(self, workflow_id: str) -> Optional[models.Workflow]:
        """Retrieves a workflow by its ID."""
        with self.session_scope() as session:
            return session.get(models.Workflow, workflow_id)

    def add_step_to_workflow(self, step_data: Dict[str, Any]) -> models.WorkflowStep:
        """Adds a new step to an existing workflow."""
        with self.session_scope() as session:
            new_step = models.WorkflowStep(**step_data)
            session.add(new_step)
            session.flush()
            session.refresh(new_step)
            return new_step

    # --- Staged Asset Operations ---

    def create_staged_asset(self, asset_data: Dict[str, Any]) -> models.StagedAsset:
        """Creates a record for a new staged asset to be reviewed."""
        with self.session_scope() as session:
            # Avoid duplicates
            existing = session.query(models.StagedAsset).filter_by(url=asset_data["url"]).one_or_none()
            if existing:
                return existing
            
            new_asset = models.StagedAsset(**asset_data)
            session.add(new_asset)
            session.flush()
            session.refresh(new_asset)
            return new_asset

    def get_pending_assets(self, limit: int = 100) -> List[models.StagedAsset]:
        """Retrieves a list of staged assets that are pending review."""
        with self.session_scope() as session:
            return session.query(models.StagedAsset).filter_by(status="pending_review").limit(limit).all()

    # --- User and Conversation Operations (from Manus) ---

    def get_or_create_user(self, user_id: str, user_data: Dict[str, Any]) -> models.User:
        """Gets a user by ID, creating them if they don't exist."""
        with self.session_scope() as session:
            user = session.get(models.User, user_id)
            if user:
                # Update if necessary
                for key, value in user_data.items():
                    setattr(user, key, value)
            else:
                user = models.User(id=user_id, **user_data)
                session.add(user)
            session.flush()
            session.refresh(user)
            return user

    def create_conversation(self, conv_data: Dict[str, Any]) -> models.Conversation:
        """Creates a new conversation for a user."""
        with self.session_scope() as session:
            new_conv = models.Conversation(**conv_data)
            session.add(new_conv)
            session.flush()
            session.refresh(new_conv)
            return new_conv

    def add_message_to_conversation(self, msg_data: Dict[str, Any]) -> models.Message:
        """Adds a message to a conversation."""
        with self.session_scope() as session:
            new_msg = models.Message(**msg_data)
            session.add(new_msg)
            session.flush()
            session.refresh(new_msg)
            return new_msg


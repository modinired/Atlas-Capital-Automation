"""
SQLite persistence layer for Terry Delmonaco Presents: AI.

This module provides minimal persistence to log scoring requests.  It uses the
standard library's sqlite3 module and stores a `scoring_log` table with one row
per call to the `/v1/risk/score` endpoint.  Each row stores a timestamp (ISO 8601
UTC), the input features as a JSON string, the resulting probability and label,
and the API key used (if any).  The database file path can be configured via
the `DB_PATH` environment variable.  If not set, a file named `data.db` in the
project root is used.

Because sqlite3 connections are not thread‑safe across threads by default, we
open a new connection per call.  For higher throughput, consider using a
connection pool or migrating to a proper relational database (e.g., PostgreSQL).
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Optional

from app.config import settings


def _get_db_path() -> str:
    return os.getenv("DB_PATH", "data.db")


def create_tables() -> None:
    """Create the scoring_log table if it does not already exist."""
    db_path = _get_db_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scoring_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                input_json TEXT NOT NULL,
                probability REAL NOT NULL,
                label INTEGER NOT NULL,
                api_key TEXT
            )
            """
        )
        conn.commit()


def log_request(features: Dict[str, float], probability: float, label: int, api_key: Optional[str]) -> None:
    """Persist a scoring request to the database.

    Args:
        features: Input feature dictionary used for scoring.
        probability: Predicted probability of the positive class.
        label: Predicted label (0 or 1).
        api_key: The API key used for the request, if any.
    """
    db_path = _get_db_path()
    ts = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO scoring_log (timestamp, input_json, probability, label, api_key) VALUES (?, ?, ?, ?, ?)",
            (ts, json.dumps(features), float(probability), int(label), api_key),
        )
        conn.commit()


async def log_request_async(features: Dict[str, float], probability: float, label: int, api_key: Optional[str]) -> None:
    """Asynchronously persist a scoring request using a thread pool.

    This wrapper offloads the synchronous sqlite3 call to a separate thread via
    asyncio.to_thread.  Using this helper prevents blocking the event loop while
    writing to the database.
    """
    import asyncio

    await asyncio.to_thread(log_request, features, probability, label, api_key)
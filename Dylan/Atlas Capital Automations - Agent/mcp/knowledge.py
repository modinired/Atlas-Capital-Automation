"""
Knowledge MCP
-------------

This module provides a simple implementation of the Knowledge MCP.
It exposes three primary functions:

* ``init_db`` – create the underlying SQLite database schema if it
  does not exist.  Called at application startup.
* ``ground`` – given a query and a logical space, return a summary
  answer, supporting evidence and coverage metrics.  Uses naive
  keyword overlap ranking over the stored documents.  In a
  production system this would be backed by a vector database and
  semantic search; here we opt for a transparent scoring approach.
* ``writeback`` – persist a list of document changesets into the
  knowledge store, capturing lineage via the provided fields.  This
  allows downstream corrections to be stored for future retrieval.
* ``snapshot`` – retrieve all documents within a particular space.

Documents are stored with the following fields:

* ``id`` – auto‑incrementing primary key
* ``space`` – namespace or tenant label (e.g. ``"crm"``, ``"finance"``)
* ``content`` – unstructured text containing the evidence
* ``created_at`` – ISO‑8601 timestamp indicating when the document
  was recorded

All functions accept an optional ``path`` argument to override the
location of the SQLite database.  The default is ``"knowledge.db"``
relative to the current working directory.

Note: this implementation is intentionally synchronous for
simplicity.  In a concurrent server environment you should use
connection pooling or an async driver (e.g. ``aiosqlite``).  The
naive similarity metric should be replaced with a proper semantic
search mechanism such as pgvector, Qdrant or Milvus, as suggested in
the architecture overview.
"""

from __future__ import annotations

import datetime
import sqlite3
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Represents a single document retrieved from the knowledge store."""

    id: int = Field(..., description="Primary key of the document")
    space: str = Field(..., description="Logical namespace for the document")
    content: str = Field(..., description="Unstructured textual content")
    created_at: str = Field(..., description="ISO‑8601 timestamp of insertion")


def init_db(path: str = "knowledge.db") -> None:
    """Create the SQLite tables if they do not already exist.

    Parameters
    ----------
    path : str, optional
        Filesystem path to the SQLite database.  Defaults to
        ``"knowledge.db"``.
    """
    con = sqlite3.connect(path)
    try:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                space TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        con.commit()
    finally:
        con.close()


def writeback(changeset: List[Dict[str, Any]], path: str = "knowledge.db") -> None:
    """Persist a list of document changes into the knowledge store.

    Each entry in ``changeset`` should contain at least a ``space`` and
    ``content`` key.  Additional keys are ignored.  A timestamp will
    be generated automatically.

    Parameters
    ----------
    changeset : list of dict
        Documents to insert into the knowledge store.  Each dict
        should have ``"space"`` and ``"content"`` keys.  If other
        fields are present they are ignored.
    path : str, optional
        Filesystem path to the SQLite database.
    """
    if not changeset:
        return
    con = sqlite3.connect(path)
    try:
        cur = con.cursor()
        for doc in changeset:
            space = doc.get("space")
            content = doc.get("content")
            if not space or not content:
                continue
            created_at = datetime.datetime.utcnow().isoformat()
            cur.execute(
                "INSERT INTO documents (space, content, created_at) VALUES (?, ?, ?)",
                (space, content, created_at),
            )
        con.commit()
    finally:
        con.close()


def _rank_documents(query: str, docs: List[sqlite3.Row]) -> List[int]:
    """Compute a naive similarity score between the query and each document.

    This helper splits the query and document content into lowercased word
    sets and computes the size of the intersection.  The indices of the
    documents are returned in descending order of score.  In the event
    of ties, the original ordering is preserved.

    Parameters
    ----------
    query : str
        The search query provided by the caller.
    docs : list of sqlite3.Row
        Rows returned from SQLite containing at least a ``content``
        field.

    Returns
    -------
    list of int
        Indices of ``docs`` sorted by descending similarity.
    """
    query_words = set(query.lower().split())
    scores = []
    for idx, row in enumerate(docs):
        doc_words = set(row[2].lower().split())
        overlap = len(query_words.intersection(doc_words))
        scores.append((overlap, idx))
    # Sort by overlap score descending; stable sort preserves original order
    scores.sort(key=lambda x: x[0], reverse=True)
    return [idx for _, idx in scores]


def ground(
    *,
    query: str,
    space: str,
    k: int = 5,
    freshness: Optional[str] = None,
    path: str = "knowledge.db",
) -> Dict[str, Any]:
    """Retrieve grounded knowledge for a given query and space.

    The ``freshness`` parameter is currently unused but is present to
    match the signature described in the architecture.  In the future it
    could be used to filter documents by age (e.g. ``"90d"``).  The
    current implementation returns the ``k`` most relevant documents by
    naive word overlap scoring and assembles an answer by concatenating
    their contents.

    Returns a dictionary with the following keys:

    * ``answer`` – concatenated string from the top documents
    * ``evidence`` – list of :class:`Evidence` objects representing the
      selected documents
    * ``coverage`` – fraction of documents retrieved relative to the
      total in the space
    * ``caveats`` – list of strings noting any retrieval caveats

    Parameters
    ----------
    query : str
        Free‑text search query.
    space : str
        Logical namespace from which to retrieve documents.
    k : int, optional
        Maximum number of documents to return.  Defaults to 5.
    freshness : str or None, optional
        Freshness filter (unused).
    path : str, optional
        Filesystem path to the SQLite database.

    Returns
    -------
    dict
    """
    con = sqlite3.connect(path)
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id, space, content, created_at FROM documents WHERE space = ?",
            (space,),
        )
        rows = cur.fetchall()
    finally:
        con.close()
    if not rows:
        return {
            "answer": "",
            "evidence": [],
            "coverage": 0.0,
            "caveats": [
                f"No evidence found in space '{space}'.  Consider writing new documents via writeback()."
            ],
        }
    order = _rank_documents(query, rows)
    selected = order[:k]
    evidence_list: List[Evidence] = []
    for idx in selected:
        row = rows[idx]
        evidence_list.append(
            Evidence(id=row[0], space=row[1], content=row[2], created_at=row[3])
        )
    answer = "\n\n".join([ev.content for ev in evidence_list])
    coverage = len(selected) / len(rows)
    return {
        "answer": answer,
        "evidence": evidence_list,
        "coverage": coverage,
        "caveats": [],
    }


def snapshot(*, entity: str, path: str = "knowledge.db") -> Dict[str, Any]:
    """Retrieve all documents in the given space.

    Parameters
    ----------
    entity : str
        Logical namespace to snapshot.
    path : str, optional
        Filesystem path to the SQLite database.

    Returns
    -------
    dict
        Contains a ``documents`` key with a list of :class:`Evidence`.
    """
    con = sqlite3.connect(path)
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id, space, content, created_at FROM documents WHERE space = ?",
            (entity,),
        )
        rows = cur.fetchall()
    finally:
        con.close()
    evidence_list = [Evidence(id=row[0], space=row[1], content=row[2], created_at=row[3]) for row in rows]
    return {"documents": evidence_list}

import sqlite3 as _sqlite3b
from pathlib import Path as _PathB
from typing import Any as _AnyB, Dict as _DictB, Optional as _OptionalB
import json as _jsonB
import time as _timeB

class TelemetryLedger:
    """Captures detailed summaries of all interactions between users, agents, and LLMs."""
    def __init__(self, db_path: str):
        self.path = _PathB(db_path)
        self.conn = _sqlite3b.connect(self.path)
        self._init()
    def _init(self) -> None:
        c = self.conn.cursor()
        c.execute("PRAGMA journal_mode=WAL;")
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                agent TEXT NOT NULL,
                role TEXT NOT NULL,
                inputs TEXT NOT NULL,
                outputs TEXT NOT NULL,
                meta TEXT NOT NULL
            );
            """
        )
        self.conn.commit()
    def log_interaction(self, *, agent: str, role: str, inputs: _DictB[str, _AnyB], outputs: _DictB[str, _AnyB] | str, meta: _DictB[str, _AnyB]) -> None:
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO interactions (ts, agent, role, inputs, outputs, meta) VALUES (?,?,?,?,?,?)",
            (int(_timeB.time()), agent, role, _jsonB.dumps(inputs, ensure_ascii=False), _jsonB.dumps(outputs, ensure_ascii=False) if not isinstance(outputs, str) else outputs, _jsonB.dumps(meta, ensure_ascii=False)),
        )
        self.conn.commit()
    def summarize(self, *, since_ts: _OptionalB[int] = None) -> dict:
        q = "SELECT ts, agent, role, inputs, outputs, meta FROM interactions"
        params: list[_AnyB] = []
        if since_ts is not None:
            q += " WHERE ts >= ?"
            params.append(int(since_ts))
        q += " ORDER BY ts ASC"
        rows = self.conn.execute(q, params).fetchall()
        def _maybe_json(s: str):
            try:
                return _jsonB.loads(s)
            except Exception:
                return s
        return {
            "count": len(rows),
            "events": [
                {"ts": r[0], "agent": r[1], "role": r[2], "inputs": _maybe_json(r[3]), "outputs": _maybe_json(r[4]), "meta": _maybe_json(r[5])}
                for r in rows
            ],
        }

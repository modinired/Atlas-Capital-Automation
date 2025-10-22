
import sqlite3 as _sqlite3
from pathlib import Path as _Path
from typing import Iterable as _Iterable, List as _List2, Tuple as _Tuple2

class KnowledgeBrain:
    """SQLite FTS5 KB for full-text recall and provenance."""
    def __init__(self, db_path: str):
        self.path = _Path(db_path)
        self.conn = _sqlite3.connect(self.path)
        self._init()
    def _init(self) -> None:
        cur = self.conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS kb USING fts5(
                doc_id UNINDEXED, title, text, source, created_at UNINDEXED
            );
            """
        )
        self.conn.commit()
    def upsert(self, rows: _Iterable[_Tuple2[str, str, str, str, str]]) -> None:
        cur = self.conn.cursor()
        cur.executemany("INSERT INTO kb (doc_id, title, text, source, created_at) VALUES (?,?,?,?,?)", rows)
        self.conn.commit()
    def search(self, query: str, k: int = 8) -> _List2[_Tuple2[str, str, str, str, str]]:
        cur = self.conn.cursor()
        cur.execute("SELECT doc_id, title, text, source, created_at FROM kb WHERE kb MATCH ? LIMIT ?", (query, k))
        return list(cur.fetchall())

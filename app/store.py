import sqlite3
import threading

from app.schemas import ClaimIn, PaperIn

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    doi TEXT,
    year INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    text TEXT NOT NULL,
    evidence TEXT NOT NULL,
    confidence REAL NOT NULL
);
"""


class Store:
    """Small SQLite-backed store. One connection, guarded by a lock so FastAPI's threads can share it."""

    def __init__(self, path: str):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._lock = threading.Lock()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def create_paper(self, data: PaperIn) -> dict:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO papers (title, doi, year) VALUES (?, ?, ?)",
                (data.title, data.doi, data.year),
            )
            self._conn.commit()
            return self._paper(cur.lastrowid)

    def list_papers(self, year: int | None, limit: int, offset: int) -> list[dict]:
        with self._lock:
            if year is None:
                rows = self._conn.execute(
                    "SELECT * FROM papers ORDER BY id LIMIT ? OFFSET ?", (limit, offset)
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM papers WHERE year = ? ORDER BY id LIMIT ? OFFSET ?",
                    (year, limit, offset),
                ).fetchall()
            return [dict(r) for r in rows]

    def get_paper(self, paper_id: int) -> dict | None:
        with self._lock:
            return self._paper(paper_id)

    def add_claim(self, paper_id: int, data: ClaimIn) -> dict | None:
        with self._lock:
            if self._paper(paper_id) is None:
                return None
            cur = self._conn.execute(
                "INSERT INTO claims (paper_id, text, evidence, confidence) VALUES (?, ?, ?, ?)",
                (paper_id, data.text, data.evidence, data.confidence),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM claims WHERE id = ?", (cur.lastrowid,)).fetchone()
            return dict(row)

    def list_claims(self, paper_id: int) -> list[dict] | None:
        with self._lock:
            if self._paper(paper_id) is None:
                return None
            rows = self._conn.execute(
                "SELECT * FROM claims WHERE paper_id = ? ORDER BY id", (paper_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def _paper(self, paper_id: int) -> dict | None:
        row = self._conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        return dict(row) if row else None

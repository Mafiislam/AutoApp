"""Small SQLite store so a job is never processed twice."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Job


class Store:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, source TEXT, title TEXT, company TEXT, url TEXT,
                score REAL, status TEXT, folder TEXT, seen_at TEXT)"""
        )
        self.db.commit()

    def known(self, job_id: str) -> bool:
        return self.db.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone() is not None

    def save(self, job: Job, status: str, folder: str = "") -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
            (job.id, job.source, job.title, job.company, job.url, job.score, status, folder,
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        self.db.commit()

    def rows(self):
        cur = self.db.execute(
            "SELECT seen_at, status, score, company, title, folder FROM jobs ORDER BY seen_at DESC")
        return cur.fetchall()

from __future__ import annotations

import sqlite3
from pathlib import Path

from jobradar.models import JobPosting, RankedJob


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS raw_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    collected_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ranked_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    score REAL NOT NULL,
                    reasons TEXT,
                    UNIQUE(title, company, url)
                );
                """
            )

    def save_raw_jobs(self, jobs: list[JobPosting]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO raw_jobs (title, company, url, source, location, description, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        job.title,
                        job.company,
                        job.url,
                        job.source,
                        job.location,
                        job.description,
                        job.collected_at,
                    )
                    for job in jobs
                ],
            )

    @staticmethod
    def deduplicate(jobs: list[JobPosting]) -> list[JobPosting]:
        unique: dict[tuple[str, str, str], JobPosting] = {}
        for job in jobs:
            key = (job.title.casefold(), job.company.casefold(), job.url.strip().casefold())
            unique[key] = job
        return list(unique.values())

    def save_ranked_jobs(self, ranked_jobs: list[RankedJob]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO ranked_jobs (title, company, url, source, score, reasons)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(title, company, url)
                DO UPDATE SET
                    score = excluded.score,
                    reasons = excluded.reasons,
                    source = excluded.source
                """,
                [
                    (
                        ranked.job.title,
                        ranked.job.company,
                        ranked.job.url,
                        ranked.job.source,
                        ranked.score,
                        "; ".join(ranked.match_reasons),
                    )
                    for ranked in ranked_jobs
                ],
            )

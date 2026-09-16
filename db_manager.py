"""
database/db_manager.py - SQLite database manager
Handles all persistence: jobs, job_history, run_history tables.
Provides duplicate detection, status tracking, and run statistics.
"""

import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA_SQL = """
-- Main jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id              TEXT UNIQUE NOT NULL,
    title               TEXT NOT NULL,
    company             TEXT NOT NULL,
    location            TEXT,
    url                 TEXT NOT NULL,
    apply_url           TEXT,
    source              TEXT NOT NULL,
    posted_date         TEXT,
    posted_date_raw     TEXT,
    description         TEXT,
    match_score         REAL DEFAULT 0,
    skill_match         REAL DEFAULT 0,
    role_match          REAL DEFAULT 0,
    experience_match    REAL DEFAULT 0,
    tool_match          REAL DEFAULT 0,
    domain_match        REAL DEFAULT 0,
    validation_status   TEXT DEFAULT 'PENDING',
    http_status_code    INTEGER,
    is_new              INTEGER DEFAULT 1,
    first_seen          TEXT NOT NULL,
    last_seen           TEXT NOT NULL,
    run_id              INTEGER,
    created_at          TEXT DEFAULT (datetime('now','localtime'))
);

-- Job history: tracks every time a job was seen
CREATE TABLE IF NOT EXISTS job_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      TEXT NOT NULL,
    run_id      INTEGER NOT NULL,
    seen_at     TEXT NOT NULL,
    status      TEXT,
    match_score REAL
);

-- Run history: one record per script execution
CREATE TABLE IF NOT EXISTS run_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date            TEXT NOT NULL,
    started_at          TEXT NOT NULL,
    finished_at         TEXT,
    jobs_crawled        INTEGER DEFAULT 0,
    jobs_validated      INTEGER DEFAULT 0,
    jobs_rejected       INTEGER DEFAULT 0,
    duplicates_removed  INTEGER DEFAULT 0,
    expired_rejected    INTEGER DEFAULT 0,
    new_jobs_added      INTEGER DEFAULT 0,
    errors              INTEGER DEFAULT 0,
    status              TEXT DEFAULT 'RUNNING'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_job_id       ON jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_url          ON jobs(url);
CREATE INDEX IF NOT EXISTS idx_jobs_source       ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date  ON jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_match_score  ON jobs(match_score);
CREATE INDEX IF NOT EXISTS idx_jobs_validation   ON jobs(validation_status);
CREATE INDEX IF NOT EXISTS idx_history_job_id    ON job_history(job_id);
CREATE INDEX IF NOT EXISTS idx_history_run_id    ON job_history(run_id);
"""


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE MANAGER CLASS
# ─────────────────────────────────────────────────────────────────────────────
class DatabaseManager:
    """
    Manages all SQLite operations for the job search system.
    Thread-safe via connection-per-call pattern.
    """

    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        self._ensure_db_dir()
        self.initialize_schema()
        logger.info(f"DatabaseManager initialized: {self.db_path}")

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _ensure_db_dir(self):
        """Create parent directory if it doesn't exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Return a new SQLite connection with row_factory set."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── Schema ────────────────────────────────────────────────────────────────

    def initialize_schema(self):
        """Create all tables and indexes if they don't exist."""
        try:
            with self._get_connection() as conn:
                conn.executescript(SCHEMA_SQL)
                conn.commit()
            logger.debug("Database schema initialized.")
        except sqlite3.Error as e:
            logger.error(f"Schema initialization failed: {e}")
            raise

    # ── Run History ───────────────────────────────────────────────────────────

    def start_run(self) -> int:
        """Insert a new run record and return its ID."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO run_history (run_date, started_at, status)
                       VALUES (?, ?, 'RUNNING')""",
                    (today, now),
                )
                conn.commit()
                run_id = cursor.lastrowid
                logger.info(f"Run started: run_id={run_id}")
                return run_id
        except sqlite3.Error as e:
            logger.error(f"Failed to start run: {e}")
            return -1

    def finish_run(self, run_id: int, stats: Dict):
        """Update run record with final statistics."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """UPDATE run_history SET
                        finished_at         = ?,
                        jobs_crawled        = ?,
                        jobs_validated      = ?,
                        jobs_rejected       = ?,
                        duplicates_removed  = ?,
                        expired_rejected    = ?,
                        new_jobs_added      = ?,
                        errors              = ?,
                        status              = 'COMPLETED'
                       WHERE id = ?""",
                    (
                        now,
                        stats.get("jobs_crawled", 0),
                        stats.get("jobs_validated", 0),
                        stats.get("jobs_rejected", 0),
                        stats.get("duplicates_removed", 0),
                        stats.get("expired_rejected", 0),
                        stats.get("new_jobs_added", 0),
                        stats.get("errors", 0),
                        run_id,
                    ),
                )
                conn.commit()
                logger.info(f"Run {run_id} finished: {stats}")
        except sqlite3.Error as e:
            logger.error(f"Failed to finish run {run_id}: {e}")

    def get_last_run_stats(self) -> Optional[Dict]:
        """Return statistics from the most recent completed run."""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    """SELECT * FROM run_history
                       WHERE status = 'COMPLETED'
                       ORDER BY id DESC LIMIT 1"""
                ).fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to get last run stats: {e}")
            return None

    # ── Duplicate Detection ───────────────────────────────────────────────────

    def is_duplicate(self, job_id: str, url: str) -> bool:
        """Return True if job_id or URL already exists in the database."""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT id FROM jobs WHERE job_id = ? OR url = ? LIMIT 1",
                    (job_id, url),
                ).fetchone()
                return row is not None
        except sqlite3.Error as e:
            logger.error(f"Duplicate check failed: {e}")
            return False

    def get_existing_urls(self) -> set:
        """Return a set of all known job URLs for fast in-memory dedup."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT url FROM jobs").fetchall()
                return {row["url"] for row in rows}
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch existing URLs: {e}")
            return set()

    def get_existing_job_ids(self) -> set:
        """Return a set of all known job IDs."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT job_id FROM jobs").fetchall()
                return {row["job_id"] for row in rows}
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch existing job IDs: {e}")
            return set()

    # ── Job CRUD ──────────────────────────────────────────────────────────────

    def insert_job(self, job: Dict, run_id: int) -> bool:
        """
        Insert a new validated job. Returns True on success.
        Marks all jobs from this run as is_new=1.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO jobs (
                        job_id, title, company, location, url, apply_url,
                        source, posted_date, posted_date_raw, description,
                        match_score, skill_match, role_match, experience_match,
                        tool_match, domain_match, validation_status,
                        http_status_code, is_new, first_seen, last_seen, run_id
                    ) VALUES (
                        :job_id, :title, :company, :location, :url, :apply_url,
                        :source, :posted_date, :posted_date_raw, :description,
                        :match_score, :skill_match, :role_match, :experience_match,
                        :tool_match, :domain_match, :validation_status,
                        :http_status_code, 1, :first_seen, :last_seen, :run_id
                    )""",
                    {
                        "job_id": job.get("job_id", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "url": job.get("url", ""),
                        "apply_url": job.get("apply_url", job.get("url", "")),
                        "source": job.get("source", ""),
                        "posted_date": job.get("posted_date", ""),
                        "posted_date_raw": job.get("posted_date_raw", ""),
                        "description": job.get("description", ""),
                        "match_score": job.get("match_score", 0),
                        "skill_match": job.get("skill_match", 0),
                        "role_match": job.get("role_match", 0),
                        "experience_match": job.get("experience_match", 0),
                        "tool_match": job.get("tool_match", 0),
                        "domain_match": job.get("domain_match", 0),
                        "validation_status": job.get("validation_status", "VALID"),
                        "http_status_code": job.get("http_status_code", 200),
                        "first_seen": now,
                        "last_seen": now,
                        "run_id": run_id,
                    },
                )
                conn.commit()

                # Also log to job_history
                conn.execute(
                    """INSERT INTO job_history (job_id, run_id, seen_at, status, match_score)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        job.get("job_id", ""),
                        run_id,
                        now,
                        job.get("validation_status", "VALID"),
                        job.get("match_score", 0),
                    ),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to insert job {job.get('job_id')}: {e}")
            return False

    def mark_old_jobs_not_new(self, run_id: int):
        """After inserting new jobs, mark all previous-run jobs as is_new=0."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET is_new = 0 WHERE run_id != ? AND is_new = 1",
                    (run_id,),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to mark old jobs: {e}")

    # ── Query Methods ─────────────────────────────────────────────────────────

    def get_jobs_for_dashboard(self, min_score: float = None, max_days: int = 30) -> List[Dict]:
        """
        Return all VALID jobs within the last max_days (default 30 days), above min_score,
        sorted by match_score DESC, then posted_date DESC.
        """
        if min_score is None:
            min_score = config.MIN_MATCH_SCORE
        cutoff = (datetime.now() - timedelta(days=max_days)).strftime(
            "%Y-%m-%d"
        )
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    """SELECT * FROM jobs
                       WHERE validation_status = 'VALID'
                         AND match_score >= ?
                         AND (posted_date >= ? OR posted_date IS NULL OR posted_date = '')
                       ORDER BY match_score DESC, posted_date DESC""",
                    (min_score, cutoff),
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch dashboard jobs: {e}")
            return []

    def get_jobs_by_date_range(self, days: int) -> List[Dict]:
        """Return VALID jobs posted within the last N days."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    """SELECT * FROM jobs
                       WHERE validation_status = 'VALID'
                         AND match_score >= ?
                         AND posted_date >= ?
                       ORDER BY match_score DESC, posted_date DESC""",
                    (config.MIN_MATCH_SCORE, cutoff),
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch jobs by date range: {e}")
            return []

    def get_top_match_jobs(self, min_score: float = 90.0) -> List[Dict]:
        """Return jobs with match_score >= min_score."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    """SELECT * FROM jobs
                       WHERE validation_status = 'VALID'
                         AND match_score >= ?
                       ORDER BY match_score DESC""",
                    (min_score,),
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch top match jobs: {e}")
            return []

    def get_new_jobs(self, run_id: int) -> List[Dict]:
        """Return jobs discovered in the current run."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    """SELECT * FROM jobs
                       WHERE run_id = ? AND validation_status = 'VALID'
                       ORDER BY match_score DESC""",
                    (run_id,),
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch new jobs: {e}")
            return []

    def get_run_statistics(self, run_id: int) -> Dict:
        """Return statistics for a specific run."""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM run_history WHERE id = ?", (run_id,)
                ).fetchone()
                return dict(row) if row else {}
        except sqlite3.Error as e:
            logger.error(f"Failed to get run statistics: {e}")
            return {}

    def cleanup_old_jobs(self, days: int = 30):
        """Remove jobs older than N days to keep the database lean."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "DELETE FROM jobs WHERE posted_date < ? AND posted_date != ''",
                    (cutoff,),
                )
                conn.commit()
                logger.info(f"Cleaned up jobs older than {days} days.")
        except sqlite3.Error as e:
            logger.error(f"Cleanup failed: {e}")

    def get_total_job_count(self) -> int:
        """Return total number of jobs in the database."""
        try:
            with self._get_connection() as conn:
                row = conn.execute("SELECT COUNT(*) as cnt FROM jobs").fetchone()
                return row["cnt"] if row else 0
        except sqlite3.Error as e:
            logger.error(f"Failed to count jobs: {e}")
            return 0

    def get_all_jobs_for_revalidation(self) -> List[Dict]:
        """Return all VALID jobs for periodic re-validation."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    """SELECT job_id, url, apply_url, title, company
                       FROM jobs
                       WHERE validation_status = 'VALID'
                       ORDER BY last_seen DESC"""
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch jobs for revalidation: {e}")
            return []

    def update_job_validation(self, job_id: str, validation_status: str,
                               http_status_code: int, validation_reason: str):
        """Update the validation status of a stored job."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """UPDATE jobs SET
                        validation_status = ?,
                        http_status_code  = ?,
                        last_seen         = ?
                       WHERE job_id = ?""",
                    (validation_status, http_status_code, now, job_id),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to update validation for {job_id}: {e}")

    def remove_invalid_jobs(self) -> int:
        """
        Delete jobs marked INVALID or EXPIRED from the database.
        Returns the number of rows deleted.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM jobs WHERE validation_status IN ('INVALID', 'EXPIRED')"
                )
                conn.commit()
                deleted = cursor.rowcount
                logger.info(f"Removed {deleted} invalid/expired jobs from database.")
                return deleted
        except sqlite3.Error as e:
            logger.error(f"Failed to remove invalid jobs: {e}")
            return 0

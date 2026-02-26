"""SQLite-based task persistence store."""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.task import ExtractedTask, Priority, TaskStatus

logger = logging.getLogger(__name__)


class TaskStore:
    """Persists extracted tasks to SQLite for history and deduplication."""

    def __init__(self, db_path: str = "data/tasks.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                source_email_id TEXT,
                source_subject TEXT,
                sender TEXT,
                sender_name TEXT,
                assignee TEXT,
                deadline TEXT,
                deadline_text TEXT,
                priority TEXT DEFAULT 'P1',
                urgency_score REAL DEFAULT 0.5,
                importance_score REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.8,
                status TEXT DEFAULT 'pending',
                tags TEXT DEFAULT '[]',
                dependencies TEXT DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT,
                emails_processed INTEGER,
                tasks_extracted INTEGER,
                p0_count INTEGER,
                p1_count INTEGER,
                p2_count INTEGER,
                p3_count INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline);
        """)
        self.conn.commit()

    def save_task(self, task: ExtractedTask) -> None:
        """Insert or update a task."""
        now = datetime.now().isoformat()
        self.conn.execute("""
            INSERT OR REPLACE INTO tasks
            (id, title, description, source_email_id, source_subject, sender, 
             sender_name, assignee, deadline, deadline_text, priority, 
             urgency_score, importance_score, confidence, status, tags, 
             dependencies, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id, task.title, task.description, task.source_email_id,
            task.source_subject, task.sender, task.sender_name, task.assignee,
            task.deadline.isoformat() if task.deadline else None,
            task.deadline_text, task.priority.value, task.urgency_score,
            task.importance_score, task.confidence, task.status.value,
            json.dumps(task.tags), json.dumps(task.dependencies),
            task.created_at.isoformat(), now,
        ))
        self.conn.commit()

    def save_tasks(self, tasks: list[ExtractedTask]) -> None:
        """Save a batch of tasks."""
        for task in tasks:
            self.save_task(task)
        logger.info(f"Saved {len(tasks)} tasks to store")

    def get_tasks(
        self,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Retrieve tasks with optional filters."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 ELSE 3 END, urgency_score DESC"
        query += f" LIMIT {limit}"

        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def log_processing_run(
        self, emails_count: int, tasks: list[ExtractedTask]
    ) -> None:
        """Log a processing run for analytics."""
        groups = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for t in tasks:
            groups[t.priority.value] = groups.get(t.priority.value, 0) + 1

        self.conn.execute("""
            INSERT INTO processing_log 
            (run_date, emails_processed, tasks_extracted, p0_count, p1_count, p2_count, p3_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(), emails_count, len(tasks),
            groups["P0"], groups["P1"], groups["P2"], groups["P3"],
        ))
        self.conn.commit()

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status."""
        self.conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, datetime.now().isoformat(), task_id),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

"""
Job queue engine using SQLite for persistent storage.
"""
import sqlite3
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JobQueue:
    """
    Lightweight in-process job queue with SQLite persistence.
    """
    
    def __init__(self, db_path: str = ".godman/state/jobs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error TEXT
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_priority 
            ON jobs(status, priority DESC, created_at)
        """)
        self.conn.commit()
    
    def enqueue(self, task_input: Any, priority: int = 1) -> int:
        """
        Add a job to the queue.
        
        Args:
            task_input: Task input (will be JSON serialized)
            priority: Job priority (higher = more important)
            
        Returns:
            Job ID
        """
        payload = json.dumps({"task_input": task_input})
        created_at = datetime.utcnow().isoformat()
        
        cursor = self.conn.execute("""
            INSERT INTO jobs (payload, priority, status, created_at)
            VALUES (?, ?, 'pending', ?)
        """, (payload, priority, created_at))
        
        self.conn.commit()
        job_id = cursor.lastrowid
        
        logger.info(f"Enqueued job {job_id} with priority {priority}")
        return job_id
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Get the next pending job (highest priority first).
        Marks job as 'running'.
        
        Returns:
            Job dict or None if queue is empty
        """
        cursor = self.conn.execute("""
            SELECT * FROM jobs
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            return None
        
        job_id = row['id']
        started_at = datetime.utcnow().isoformat()
        
        self.conn.execute("""
            UPDATE jobs
            SET status = 'running', started_at = ?
            WHERE id = ?
        """, (started_at, job_id))
        self.conn.commit()
        
        job = dict(row)
        job['payload'] = json.loads(job['payload'])
        
        logger.debug(f"Dequeued job {job_id}")
        return job
    
    def mark_complete(self, job_id: int, error: Optional[str] = None):
        """
        Mark a job as complete or failed.
        
        Args:
            job_id: Job ID
            error: Error message if job failed
        """
        completed_at = datetime.utcnow().isoformat()
        status = 'failed' if error else 'completed'
        
        self.conn.execute("""
            UPDATE jobs
            SET status = ?, completed_at = ?, error = ?
            WHERE id = ?
        """, (status, completed_at, error, job_id))
        self.conn.commit()
        
        logger.info(f"Job {job_id} marked as {status}")
    
    def size(self) -> int:
        """Get number of pending jobs."""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as count FROM jobs WHERE status = 'pending'
        """)
        return cursor.fetchone()['count']
    
    def get_status(self) -> Dict[str, int]:
        """Get count of jobs by status."""
        cursor = self.conn.execute("""
            SELECT status, COUNT(*) as count
            FROM jobs
            GROUP BY status
        """)
        return {row['status']: row['count'] for row in cursor.fetchall()}
    
    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        cursor = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        job = dict(row)
        job['payload'] = json.loads(job['payload'])
        return job
    
    def clear(self, status: Optional[str] = None):
        """
        Clear jobs from queue.
        
        Args:
            status: If provided, only clear jobs with this status
        """
        if status:
            self.conn.execute("DELETE FROM jobs WHERE status = ?", (status,))
        else:
            self.conn.execute("DELETE FROM jobs")
        self.conn.commit()
        logger.info(f"Cleared jobs" + (f" with status {status}" if status else ""))
    
    def close(self):
        """Close database connection."""
        self.conn.close()

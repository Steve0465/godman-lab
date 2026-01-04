"""
Task Manager for scheduled and on-demand task execution.

Provides persistence and management for scheduled tasks using SQLite.
"""
import sqlite3
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """A scheduled task with metadata."""
    id: int
    task_input: str
    schedule_type: str  # 'now', 'hourly', 'daily', 'cron'
    schedule_value: Optional[str] = None  # Cron expression or time for daily
    status: str = 'pending'  # 'pending', 'active', 'paused', 'completed', 'failed'
    priority: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


class TaskManager:
    """
    Manages scheduled and on-demand tasks with SQLite persistence.
    Integrates with the existing Scheduler and JobQueue.
    """
    
    def __init__(self, db_path: str = ".godman/state/tasks.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_input TEXT NOT NULL,
                schedule_type TEXT NOT NULL,
                schedule_value TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                last_run TEXT,
                next_run TEXT,
                run_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_next_run 
            ON scheduled_tasks(status, next_run)
        """)
        self.conn.commit()
    
    def create_task(
        self,
        task_input: str,
        schedule_type: str,
        schedule_value: Optional[str] = None,
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a new scheduled task.
        
        Args:
            task_input: Task input/command to execute
            schedule_type: Type of schedule ('now', 'hourly', 'daily', 'cron')
            schedule_value: Schedule value (cron expression for 'cron', time for 'daily')
            priority: Task priority (higher = more important)
            metadata: Optional metadata dict
            
        Returns:
            Task ID
            
        Raises:
            ValueError: If schedule type or value is invalid
        """
        # Validate schedule type
        valid_types = ['now', 'hourly', 'daily', 'cron']
        if schedule_type not in valid_types:
            raise ValueError(f"Invalid schedule type. Must be one of: {valid_types}")
        
        # Calculate next run time
        next_run = self._calculate_next_run(schedule_type, schedule_value)
        
        created_at = datetime.now(timezone.utc).isoformat()
        status = 'active' if schedule_type != 'now' else 'pending'
        
        cursor = self.conn.execute("""
            INSERT INTO scheduled_tasks (
                task_input, schedule_type, schedule_value, status, priority,
                created_at, next_run, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_input,
            schedule_type,
            schedule_value,
            status,
            priority,
            created_at,
            next_run,
            json.dumps(metadata) if metadata else None
        ))
        
        self.conn.commit()
        task_id = cursor.lastrowid
        
        logger.info(f"Created task {task_id}: {schedule_type} - {task_input}")
        
        # If schedule type is 'now', enqueue immediately
        if schedule_type == 'now':
            self._execute_task(task_id)
        
        return task_id
    
    def _calculate_next_run(
        self,
        schedule_type: str,
        schedule_value: Optional[str] = None
    ) -> Optional[str]:
        """Calculate next run time based on schedule type and value."""
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        
        if schedule_type == 'now':
            return now.isoformat()
        elif schedule_type == 'hourly':
            # Run at the top of the next hour
            next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            return next_run.isoformat()
        elif schedule_type == 'daily':
            # Run daily at specified time (default 00:00)
            if schedule_value:
                try:
                    # Parse time in HH:MM format
                    parts = schedule_value.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    
                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    return next_run.isoformat()
                except (ValueError, IndexError):
                    raise ValueError(f"Invalid daily time format: {schedule_value}. Use HH:MM")
            else:
                # Default to midnight
                next_run = now.replace(hour=0, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run.isoformat()
        elif schedule_type == 'cron':
            if not schedule_value:
                raise ValueError("Cron schedule type requires a cron expression")
            
            # Use cron parser to calculate next run
            # Import here to avoid circular dependency with scheduler module
            from godman_ai.scheduler.cron_parser import parse_cron
            parser = parse_cron(schedule_value)
            
            if not parser.is_valid():
                raise ValueError(f"Invalid cron expression: {schedule_value}")
            
            next_run = parser.get_next()
            return next_run.isoformat() if next_run else None
        
        return None
    
    def _execute_task(self, task_id: int):
        """Execute a task by enqueueing it."""
        from godman_ai.queue.job_queue import JobQueue
        
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        # Enqueue the task
        queue = JobQueue()
        job_id = queue.enqueue(task['task_input'], priority=task['priority'])
        
        # Update task metadata
        now = datetime.now(timezone.utc).isoformat()
        run_count = task['run_count'] + 1
        
        # Calculate next run for recurring tasks
        next_run = None
        if task['schedule_type'] in ['hourly', 'daily', 'cron']:
            next_run = self._calculate_next_run(task['schedule_type'], task['schedule_value'])
        else:
            # One-time task, mark as completed
            self.conn.execute("""
                UPDATE scheduled_tasks
                SET status = 'completed', last_run = ?, run_count = ?, updated_at = ?
                WHERE id = ?
            """, (now, run_count, now, task_id))
            self.conn.commit()
            return
        
        # Update recurring task
        self.conn.execute("""
            UPDATE scheduled_tasks
            SET last_run = ?, next_run = ?, run_count = ?, updated_at = ?
            WHERE id = ?
        """, (now, next_run, run_count, now, task_id))
        self.conn.commit()
        
        logger.info(f"Executed task {task_id}, created job {job_id}")
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM scheduled_tasks WHERE id = ?",
            (task_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        task = dict(row)
        if task.get('metadata'):
            task['metadata'] = json.loads(task['metadata'])
        
        return task
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        schedule_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering.
        
        Args:
            status: Filter by status
            schedule_type: Filter by schedule type
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            
        Returns:
            List of task dicts
        """
        query = "SELECT * FROM scheduled_tasks WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if schedule_type:
            query += " AND schedule_type = ?"
            params.append(schedule_type)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = self.conn.execute(query, params)
        
        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            if task.get('metadata'):
                task['metadata'] = json.loads(task['metadata'])
            tasks.append(task)
        
        return tasks
    
    def update_task(
        self,
        task_id: int,
        schedule_type: Optional[str] = None,
        schedule_value: Optional[str] = None,
        priority: Optional[int] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a task.
        
        Args:
            task_id: Task ID
            schedule_type: New schedule type
            schedule_value: New schedule value
            priority: New priority
            status: New status
            metadata: New metadata
            
        Returns:
            True if updated, False if not found
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        updates = []
        params = []
        
        if schedule_type is not None:
            updates.append("schedule_type = ?")
            params.append(schedule_type)
        
        if schedule_value is not None:
            updates.append("schedule_value = ?")
            params.append(schedule_value)
        
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        
        if not updates:
            return True
        
        # Recalculate next run if schedule changed
        if schedule_type is not None or schedule_value is not None:
            new_schedule_type = schedule_type if schedule_type is not None else task['schedule_type']
            new_schedule_value = schedule_value if schedule_value is not None else task['schedule_value']
            next_run = self._calculate_next_run(new_schedule_type, new_schedule_value)
            updates.append("next_run = ?")
            params.append(next_run)
        
        # Add updated_at
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        
        # Add task_id for WHERE clause
        params.append(task_id)
        
        query = f"UPDATE scheduled_tasks SET {', '.join(updates)} WHERE id = ?"
        self.conn.execute(query, params)
        self.conn.commit()
        
        logger.info(f"Updated task {task_id}")
        return True
    
    def delete_task(self, task_id: int) -> bool:
        """
        Delete/cancel a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM scheduled_tasks WHERE id = ?",
            (task_id,)
        )
        self.conn.commit()
        
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted task {task_id}")
        
        return deleted
    
    def run_pending_tasks(self):
        """Check for pending tasks and execute them."""
        now = datetime.now(timezone.utc).isoformat()
        
        # Find tasks that are due
        cursor = self.conn.execute("""
            SELECT id FROM scheduled_tasks
            WHERE status = 'active' AND next_run <= ?
        """, (now,))
        
        task_ids = [row['id'] for row in cursor.fetchall()]
        
        for task_id in task_ids:
            try:
                self._execute_task(task_id)
            except Exception as e:
                logger.error(f"Error executing task {task_id}: {e}", exc_info=True)
    
    def close(self):
        """Close database connection."""
        self.conn.close()

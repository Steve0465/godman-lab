"""
Tests for TaskManager subsystem.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta


@pytest.fixture
def temp_task_db():
    """Create temporary database for task manager tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_tasks.db"
    yield str(db_path)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_job_db():
    """Create temporary database for job queue tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_jobs.db"
    yield str(db_path)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_task_manager_create_now_task(temp_task_db, temp_job_db):
    """Test creating a task with 'now' schedule type."""
    from godman_ai.scheduler.task_manager import TaskManager
    from godman_ai.queue import job_queue
    
    # Need to patch the JobQueue path
    original_init = job_queue.JobQueue.__init__
    
    def patched_init(self, db_path=None):
        original_init(self, db_path=temp_job_db)
    
    job_queue.JobQueue.__init__ = patched_init
    
    try:
        manager = TaskManager(db_path=temp_task_db)
        
        task_id = manager.create_task(
            task_input="test command",
            schedule_type="now",
            priority=5
        )
        
        assert task_id > 0
        
        task = manager.get_task(task_id)
        assert task is not None
        assert task['task_input'] == "test command"
        assert task['schedule_type'] == "now"
        assert task['status'] == "completed"
        assert task['run_count'] == 1
    finally:
        job_queue.JobQueue.__init__ = original_init


def test_task_manager_create_hourly_task(temp_task_db):
    """Test creating a task with 'hourly' schedule type."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    task_id = manager.create_task(
        task_input="hourly task",
        schedule_type="hourly"
    )
    
    assert task_id > 0
    
    task = manager.get_task(task_id)
    assert task is not None
    assert task['schedule_type'] == "hourly"
    assert task['status'] == "active"
    assert task['next_run'] is not None


def test_task_manager_create_daily_task(temp_task_db):
    """Test creating a task with 'daily' schedule type."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    task_id = manager.create_task(
        task_input="daily task",
        schedule_type="daily",
        schedule_value="14:30"
    )
    
    assert task_id > 0
    
    task = manager.get_task(task_id)
    assert task is not None
    assert task['schedule_type'] == "daily"
    assert task['schedule_value'] == "14:30"
    assert task['status'] == "active"
    
    # Verify next run is at 14:30
    next_run = datetime.fromisoformat(task['next_run'])
    assert next_run.hour == 14
    assert next_run.minute == 30


def test_task_manager_create_cron_task(temp_task_db):
    """Test creating a task with 'cron' schedule type."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    task_id = manager.create_task(
        task_input="cron task",
        schedule_type="cron",
        schedule_value="*/15 * * * *"
    )
    
    assert task_id > 0
    
    task = manager.get_task(task_id)
    assert task is not None
    assert task['schedule_type'] == "cron"
    assert task['schedule_value'] == "*/15 * * * *"
    assert task['status'] == "active"


def test_task_manager_invalid_schedule_type(temp_task_db):
    """Test that invalid schedule types are rejected."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    with pytest.raises(ValueError, match="Invalid schedule type"):
        manager.create_task(
            task_input="test",
            schedule_type="invalid"
        )


def test_task_manager_invalid_cron(temp_task_db):
    """Test that invalid cron expressions are rejected."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    with pytest.raises(ValueError, match="Invalid cron expression"):
        manager.create_task(
            task_input="test",
            schedule_type="cron",
            schedule_value="invalid cron"
        )


def test_task_manager_list_tasks(temp_task_db):
    """Test listing tasks."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    # Create several tasks
    manager.create_task("task 1", "hourly")
    manager.create_task("task 2", "daily", "10:00")
    manager.create_task("task 3", "cron", "0 * * * *")
    
    tasks = manager.list_tasks()
    assert len(tasks) == 3
    
    # Test filtering by schedule type
    hourly_tasks = manager.list_tasks(schedule_type="hourly")
    assert len(hourly_tasks) == 1
    assert hourly_tasks[0]['task_input'] == "task 1"


def test_task_manager_update_task(temp_task_db):
    """Test updating a task."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    task_id = manager.create_task(
        task_input="original task",
        schedule_type="hourly",
        priority=1
    )
    
    # Update priority and status
    updated = manager.update_task(
        task_id=task_id,
        priority=5,
        status="paused"
    )
    
    assert updated is True
    
    task = manager.get_task(task_id)
    assert task['priority'] == 5
    assert task['status'] == "paused"


def test_task_manager_delete_task(temp_task_db):
    """Test deleting a task."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    task_id = manager.create_task("task to delete", "hourly")
    
    deleted = manager.delete_task(task_id)
    assert deleted is True
    
    task = manager.get_task(task_id)
    assert task is None


def test_task_manager_with_metadata(temp_task_db):
    """Test creating a task with metadata."""
    from godman_ai.scheduler.task_manager import TaskManager
    
    manager = TaskManager(db_path=temp_task_db)
    
    metadata = {
        "source": "api",
        "user_id": 123,
        "tags": ["important", "urgent"]
    }
    
    task_id = manager.create_task(
        task_input="task with metadata",
        schedule_type="daily",
        schedule_value="09:00",
        metadata=metadata
    )
    
    task = manager.get_task(task_id)
    assert task['metadata'] == metadata

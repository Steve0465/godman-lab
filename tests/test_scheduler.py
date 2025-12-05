"""
Tests for scheduler subsystem.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime


@pytest.fixture
def temp_schedule_file():
    """Create temporary schedule file."""
    temp_dir = tempfile.mkdtemp()
    schedule_file = Path(temp_dir) / "schedules.json"
    yield str(schedule_file)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_cron_parser_every_minute():
    """Test cron parser for simple every-N-minutes expression."""
    from godman_ai.scheduler import parse_cron
    
    parser = parse_cron("*/5 * * * *")
    
    assert parser.is_valid()
    
    next_run = parser.get_next()
    assert next_run is not None
    assert isinstance(next_run, datetime)


def test_cron_parser_daily():
    """Test cron parser for daily at specific time."""
    from godman_ai.scheduler import parse_cron
    
    parser = parse_cron("30 14 * * *")  # Daily at 14:30
    
    assert parser.is_valid()
    
    next_run = parser.get_next()
    assert next_run is not None
    assert next_run.hour == 14
    assert next_run.minute == 30


def test_scheduler_add_schedule(temp_schedule_file):
    """Test adding a schedule."""
    from godman_ai.scheduler import Scheduler
    
    scheduler = Scheduler(schedule_file=temp_schedule_file)
    
    schedule_id = scheduler.add_schedule(
        cron="*/10 * * * *",
        command="process receipts"
    )
    
    assert schedule_id > 0
    
    schedules = scheduler.get_schedules()
    assert len(schedules) == 1
    assert schedules[0].cron == "*/10 * * * *"
    assert schedules[0].command == "process receipts"


def test_scheduler_remove_schedule(temp_schedule_file):
    """Test removing a schedule."""
    from godman_ai.scheduler import Scheduler
    
    scheduler = Scheduler(schedule_file=temp_schedule_file)
    
    schedule_id = scheduler.add_schedule("*/5 * * * *", "test command")
    
    removed = scheduler.remove_schedule(schedule_id)
    assert removed is True
    
    schedules = scheduler.get_schedules()
    assert len(schedules) == 0


def test_scheduler_enable_disable(temp_schedule_file):
    """Test enabling/disabling schedules."""
    from godman_ai.scheduler import Scheduler
    
    scheduler = Scheduler(schedule_file=temp_schedule_file)
    
    schedule_id = scheduler.add_schedule("*/5 * * * *", "test command")
    
    # Disable
    scheduler.enable_schedule(schedule_id, enabled=False)
    schedules = scheduler.get_schedules()
    assert schedules[0].enabled is False
    
    # Enable
    scheduler.enable_schedule(schedule_id, enabled=True)
    schedules = scheduler.get_schedules()
    assert schedules[0].enabled is True


def test_scheduler_invalid_cron(temp_schedule_file):
    """Test that invalid cron expressions are rejected."""
    from godman_ai.scheduler import Scheduler
    
    scheduler = Scheduler(schedule_file=temp_schedule_file)
    
    with pytest.raises(ValueError):
        scheduler.add_schedule("invalid cron", "test command")


def test_scheduler_run_pending(temp_schedule_file, temp_db):
    """Test running pending schedules."""
    from godman_ai.scheduler import Scheduler
    from godman_ai.queue import JobQueue
    
    scheduler = Scheduler(schedule_file=temp_schedule_file)
    queue = JobQueue(db_path=temp_db)
    
    # Add a schedule (it won't trigger immediately)
    scheduler.add_schedule("*/5 * * * *", "test command")
    
    # Run pending (should not enqueue anything yet)
    scheduler.run_pending(queue=queue)
    
    # Queue should still be empty (no schedules are due yet)
    assert queue.size() == 0


def test_scheduler_persistence(temp_schedule_file):
    """Test that schedules persist across instances."""
    from godman_ai.scheduler import Scheduler
    
    # Create scheduler and add schedule
    scheduler1 = Scheduler(schedule_file=temp_schedule_file)
    schedule_id = scheduler1.add_schedule("*/5 * * * *", "test command")
    
    # Create new scheduler instance
    scheduler2 = Scheduler(schedule_file=temp_schedule_file)
    schedules = scheduler2.get_schedules()
    
    assert len(schedules) == 1
    assert schedules[0].id == schedule_id


@pytest.fixture
def temp_db():
    """Create temporary database for queue tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_jobs.db"
    yield str(db_path)
    shutil.rmtree(temp_dir, ignore_errors=True)

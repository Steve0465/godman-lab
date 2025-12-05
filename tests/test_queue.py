"""
Tests for job queue subsystem.
"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_db():
    """Create temporary database."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_jobs.db"
    yield str(db_path)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_job_queue_basic(temp_db):
    """Test basic job queue operations."""
    from godman_ai.queue import JobQueue
    
    queue = JobQueue(db_path=temp_db)
    
    # Test enqueue
    job_id = queue.enqueue("test task", priority=1)
    assert job_id > 0
    
    # Test size
    assert queue.size() == 1
    
    # Test dequeue
    job = queue.dequeue()
    assert job is not None
    assert job['id'] == job_id
    assert job['payload']['task_input'] == "test task"
    assert job['status'] == 'running'
    
    # Queue should be empty now
    assert queue.size() == 0


def test_job_queue_priority(temp_db):
    """Test job priority ordering."""
    from godman_ai.queue import JobQueue
    
    queue = JobQueue(db_path=temp_db)
    
    # Enqueue with different priorities
    job1 = queue.enqueue("low priority", priority=1)
    job2 = queue.enqueue("high priority", priority=10)
    job3 = queue.enqueue("medium priority", priority=5)
    
    # Dequeue should return highest priority first
    job = queue.dequeue()
    assert job['id'] == job2  # High priority
    
    job = queue.dequeue()
    assert job['id'] == job3  # Medium priority
    
    job = queue.dequeue()
    assert job['id'] == job1  # Low priority


def test_job_queue_completion(temp_db):
    """Test marking jobs as complete or failed."""
    from godman_ai.queue import JobQueue
    
    queue = JobQueue(db_path=temp_db)
    
    job_id = queue.enqueue("test task")
    job = queue.dequeue()
    
    # Mark as complete
    queue.mark_complete(job_id)
    
    # Get job status
    job_data = queue.get_job(job_id)
    assert job_data['status'] == 'completed'
    assert job_data['completed_at'] is not None


def test_job_queue_failure(temp_db):
    """Test marking jobs as failed with error."""
    from godman_ai.queue import JobQueue
    
    queue = JobQueue(db_path=temp_db)
    
    job_id = queue.enqueue("test task")
    job = queue.dequeue()
    
    # Mark as failed
    error_msg = "Something went wrong"
    queue.mark_complete(job_id, error=error_msg)
    
    # Get job status
    job_data = queue.get_job(job_id)
    assert job_data['status'] == 'failed'
    assert job_data['error'] == error_msg


def test_job_queue_status(temp_db):
    """Test getting queue status summary."""
    from godman_ai.queue import JobQueue
    
    queue = JobQueue(db_path=temp_db)
    
    # Add various jobs
    queue.enqueue("task1")
    queue.enqueue("task2")
    job = queue.dequeue()
    queue.mark_complete(job['id'])
    
    status = queue.get_status()
    
    assert status.get('pending', 0) == 1
    assert status.get('completed', 0) == 1


def test_job_worker_process_job(temp_db):
    """Test job worker processing (without actual agent loop)."""
    from godman_ai.queue import JobQueue, JobWorker
    
    queue = JobQueue(db_path=temp_db)
    worker = JobWorker(queue=queue)
    
    # Enqueue a job
    job_id = queue.enqueue("test task")
    
    # Note: run_once will fail without agent_loop implementation
    # This just tests the structure exists
    assert hasattr(worker, 'run_once')
    assert hasattr(worker, 'run_forever')
    assert hasattr(worker, 'process_job')

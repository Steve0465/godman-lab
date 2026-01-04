"""
Tests for Task API endpoints.
"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_task_db():
    """Create temporary database for task tests."""
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


def test_task_create_endpoint_hourly(temp_task_db, temp_job_db):
    """Test POST /task endpoint with hourly schedule."""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        import godman_ai.scheduler.task_manager as tm_module
        import godman_ai.queue.job_queue as jq_module
        
        # Patch database paths
        original_tm_init = tm_module.TaskManager.__init__
        original_jq_init = jq_module.JobQueue.__init__
        
        def patched_tm_init(self, db_path=None):
            original_tm_init(self, db_path=temp_task_db)
        
        def patched_jq_init(self, db_path=None):
            original_jq_init(self, db_path=temp_job_db)
        
        tm_module.TaskManager.__init__ = patched_tm_init
        jq_module.JobQueue.__init__ = patched_jq_init
        
        try:
            client = TestClient(app)
            
            response = client.post("/task", json={
                "task_input": "test hourly task",
                "schedule_type": "hourly",
                "priority": 3
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "task_id" in data
            assert data["task"]["schedule_type"] == "hourly"
            assert data["task"]["status"] == "active"
        finally:
            tm_module.TaskManager.__init__ = original_tm_init
            jq_module.JobQueue.__init__ = original_jq_init
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_task_create_endpoint_daily(temp_task_db, temp_job_db):
    """Test POST /task endpoint with daily schedule."""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        import godman_ai.scheduler.task_manager as tm_module
        import godman_ai.queue.job_queue as jq_module
        
        # Patch database paths
        original_tm_init = tm_module.TaskManager.__init__
        original_jq_init = jq_module.JobQueue.__init__
        
        def patched_tm_init(self, db_path=None):
            original_tm_init(self, db_path=temp_task_db)
        
        def patched_jq_init(self, db_path=None):
            original_jq_init(self, db_path=temp_job_db)
        
        tm_module.TaskManager.__init__ = patched_tm_init
        jq_module.JobQueue.__init__ = patched_jq_init
        
        try:
            client = TestClient(app)
            
            response = client.post("/task", json={
                "task_input": "daily backup",
                "schedule_type": "daily",
                "schedule_value": "02:00"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["task"]["schedule_type"] == "daily"
            assert data["task"]["schedule_value"] == "02:00"
        finally:
            tm_module.TaskManager.__init__ = original_tm_init
            jq_module.JobQueue.__init__ = original_jq_init
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_task_list_endpoint(temp_task_db, temp_job_db):
    """Test GET /task endpoint."""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        import godman_ai.scheduler.task_manager as tm_module
        import godman_ai.queue.job_queue as jq_module
        
        # Patch database paths
        original_tm_init = tm_module.TaskManager.__init__
        original_jq_init = jq_module.JobQueue.__init__
        
        def patched_tm_init(self, db_path=None):
            original_tm_init(self, db_path=temp_task_db)
        
        def patched_jq_init(self, db_path=None):
            original_jq_init(self, db_path=temp_job_db)
        
        tm_module.TaskManager.__init__ = patched_tm_init
        jq_module.JobQueue.__init__ = patched_jq_init
        
        try:
            client = TestClient(app)
            
            # Create some tasks
            client.post("/task", json={
                "task_input": "task 1",
                "schedule_type": "hourly"
            })
            client.post("/task", json={
                "task_input": "task 2",
                "schedule_type": "daily",
                "schedule_value": "10:00"
            })
            
            # List all tasks
            response = client.get("/task")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "tasks" in data
            assert data["count"] >= 2
        finally:
            tm_module.TaskManager.__init__ = original_tm_init
            jq_module.JobQueue.__init__ = original_jq_init
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_task_get_endpoint(temp_task_db, temp_job_db):
    """Test GET /task/{task_id} endpoint."""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        import godman_ai.scheduler.task_manager as tm_module
        import godman_ai.queue.job_queue as jq_module
        
        # Patch database paths
        original_tm_init = tm_module.TaskManager.__init__
        original_jq_init = jq_module.JobQueue.__init__
        
        def patched_tm_init(self, db_path=None):
            original_tm_init(self, db_path=temp_task_db)
        
        def patched_jq_init(self, db_path=None):
            original_jq_init(self, db_path=temp_job_db)
        
        tm_module.TaskManager.__init__ = patched_tm_init
        jq_module.JobQueue.__init__ = patched_jq_init
        
        try:
            client = TestClient(app)
            
            # Create a task
            create_response = client.post("/task", json={
                "task_input": "get test task",
                "schedule_type": "hourly"
            })
            task_id = create_response.json()["task_id"]
            
            # Get the task
            response = client.get(f"/task/{task_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["task"]["id"] == task_id
            assert data["task"]["task_input"] == "get test task"
        finally:
            tm_module.TaskManager.__init__ = original_tm_init
            jq_module.JobQueue.__init__ = original_jq_init
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_task_update_endpoint(temp_task_db, temp_job_db):
    """Test PUT /task/{task_id} endpoint."""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        import godman_ai.scheduler.task_manager as tm_module
        import godman_ai.queue.job_queue as jq_module
        
        # Patch database paths
        original_tm_init = tm_module.TaskManager.__init__
        original_jq_init = jq_module.JobQueue.__init__
        
        def patched_tm_init(self, db_path=None):
            original_tm_init(self, db_path=temp_task_db)
        
        def patched_jq_init(self, db_path=None):
            original_jq_init(self, db_path=temp_job_db)
        
        tm_module.TaskManager.__init__ = patched_tm_init
        jq_module.JobQueue.__init__ = patched_jq_init
        
        try:
            client = TestClient(app)
            
            # Create a task
            create_response = client.post("/task", json={
                "task_input": "update test task",
                "schedule_type": "hourly",
                "priority": 1
            })
            task_id = create_response.json()["task_id"]
            
            # Update the task
            response = client.put(f"/task/{task_id}", json={
                "priority": 10,
                "status": "paused"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["task"]["priority"] == 10
            assert data["task"]["status"] == "paused"
        finally:
            tm_module.TaskManager.__init__ = original_tm_init
            jq_module.JobQueue.__init__ = original_jq_init
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_task_delete_endpoint(temp_task_db, temp_job_db):
    """Test DELETE /task/{task_id} endpoint."""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        import godman_ai.scheduler.task_manager as tm_module
        import godman_ai.queue.job_queue as jq_module
        
        # Patch database paths
        original_tm_init = tm_module.TaskManager.__init__
        original_jq_init = jq_module.JobQueue.__init__
        
        def patched_tm_init(self, db_path=None):
            original_tm_init(self, db_path=temp_task_db)
        
        def patched_jq_init(self, db_path=None):
            original_jq_init(self, db_path=temp_job_db)
        
        tm_module.TaskManager.__init__ = patched_tm_init
        jq_module.JobQueue.__init__ = patched_jq_init
        
        try:
            client = TestClient(app)
            
            # Create a task
            create_response = client.post("/task", json={
                "task_input": "delete test task",
                "schedule_type": "daily",
                "schedule_value": "12:00"
            })
            task_id = create_response.json()["task_id"]
            
            # Delete the task
            response = client.delete(f"/task/{task_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Verify it's gone
            get_response = client.get(f"/task/{task_id}")
            assert get_response.status_code == 404
        finally:
            tm_module.TaskManager.__init__ = original_tm_init
            jq_module.JobQueue.__init__ = original_jq_init
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_task_invalid_schedule_type(temp_task_db, temp_job_db):
    """Test that invalid schedule type returns 400."""
    try:
        from fastapi.testclient import TestClient
        from godman_ai.service.api import app
        import godman_ai.scheduler.task_manager as tm_module
        import godman_ai.queue.job_queue as jq_module
        
        # Patch database paths
        original_tm_init = tm_module.TaskManager.__init__
        original_jq_init = jq_module.JobQueue.__init__
        
        def patched_tm_init(self, db_path=None):
            original_tm_init(self, db_path=temp_task_db)
        
        def patched_jq_init(self, db_path=None):
            original_jq_init(self, db_path=temp_job_db)
        
        tm_module.TaskManager.__init__ = patched_tm_init
        jq_module.JobQueue.__init__ = patched_jq_init
        
        try:
            client = TestClient(app)
            
            response = client.post("/task", json={
                "task_input": "invalid task",
                "schedule_type": "invalid_type"
            })
            
            assert response.status_code == 400
        finally:
            tm_module.TaskManager.__init__ = original_tm_init
            jq_module.JobQueue.__init__ = original_jq_init
    except ImportError:
        pytest.skip("FastAPI not installed")

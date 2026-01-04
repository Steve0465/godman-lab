"""
FastAPI-based HTTP API for GodmanAI

Provides REST endpoints for orchestrator, agents, queue, memory, and system state.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _lazy_imports():
    """Lazy import heavy dependencies"""
    try:
        from fastapi import FastAPI, HTTPException, Header, status
        from fastapi.responses import JSONResponse, HTMLResponse
        from pydantic import BaseModel
        return FastAPI, HTTPException, JSONResponse, HTMLResponse, BaseModel, Header, status
    except ImportError:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")


# Initialize FastAPI app
FastAPI, HTTPException, JSONResponse, HTMLResponse, BaseModel, Header, status = _lazy_imports()
app = FastAPI(title="GodmanAI API", version="1.0.0")


# Global settings holder (loaded on demand)
_settings = None


def get_settings():
    """Lazy load settings"""
    global _settings
    if _settings is None:
        from godman_ai.config.loader import load_settings
        _settings = load_settings()
        
        # Log warning if API token is missing
        if not _settings.api_token:
            logger.warning("API token not configured. Set GODMAN_API_TOKEN environment variable for secure API access.")
    
    return _settings


def verify_token(authorization: Optional[str] = Header(None)):
    """Verify bearer token for mutating endpoints"""
    settings = get_settings()
    
    # If no token configured, allow access (with warning already logged)
    if not settings.api_token:
        return
    
    # Check authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify token
    if token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Request models
class RunRequest(BaseModel):
    input: str


class AgentRequest(BaseModel):
    input: str


class EnqueueRequest(BaseModel):
    task_input: str
    priority: int = 1


class MemoryAddRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None


class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = 5


class TaskCreateRequest(BaseModel):
    task_input: str
    schedule_type: str  # 'now', 'hourly', 'daily', 'cron'
    schedule_value: Optional[str] = None
    priority: int = 1
    metadata: Optional[Dict[str, Any]] = None


class TaskUpdateRequest(BaseModel):
    schedule_type: Optional[str] = None
    schedule_value: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "GodmanAI API Server", "version": "1.0.0"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Web dashboard"""
    from godman_ai.service.dashboard import get_dashboard_html
    return get_dashboard_html()


@app.post("/run")
def run_orchestrator(request: RunRequest, _: None = Header(None, alias="Authorization", include_in_schema=False, dependencies=[verify_token])):
    """Run orchestrator directly on input"""
    try:
        from godman_ai.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        orchestrator.load_tools_from_package("godman_ai.tools")
        
        result = orchestrator.run_task(request.input)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error in /run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent")
def run_agent(request: AgentRequest, authorization: Optional[str] = Header(None)):
    """Run full AgentLoop on input"""
    verify_token(authorization)
    
    try:
        from godman_ai.agents.agent_loop import AgentLoop
        
        loop = AgentLoop()
        result = loop.run(request.input)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error in /agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/queue/enqueue")
def enqueue_job(request: EnqueueRequest, authorization: Optional[str] = Header(None)):
    """Add job to queue"""
    verify_token(authorization)
    
    try:
        from godman_ai.queue.job_queue import JobQueue
        
        queue = JobQueue()
        job_id = queue.enqueue(request.task_input, priority=request.priority)
        return {"success": True, "job_id": job_id}
    except Exception as e:
        logger.error(f"Error in /queue/enqueue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/status")
def queue_status():
    """Get queue status"""
    try:
        from godman_ai.queue.job_queue import JobQueue
        
        queue = JobQueue()
        return {
            "size": queue.size(),
            "pending": queue.size()
        }
    except Exception as e:
        logger.error(f"Error in /queue/status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/os/state")
def os_state():
    """Get OS Core state snapshot"""
    try:
        from godman_ai.os_core.state_manager import GlobalState
        
        state = GlobalState()
        return state.snapshot()
    except Exception as e:
        logger.error(f"Error in /os/state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/os/health")
def os_health():
    """Get system health metrics"""
    try:
        from godman_ai.os_core.health import system_health
        
        return system_health()
    except Exception as e:
        logger.error(f"Error in /os/health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
def list_tools():
    """List all registered tools"""
    try:
        from godman_ai.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        orchestrator.load_tools_from_package("godman_ai.tools")
        
        tools = []
        for name, tool_cls in orchestrator.tools.items():
            tools.append({
                "name": name,
                "description": getattr(tool_cls, "description", "")
            })
        
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error in /tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
def list_models():
    """List available models"""
    try:
        from godman_ai.os_core.model_router import ModelRouter
        
        router = ModelRouter()
        return {"models": router.available_models()}
    except Exception as e:
        logger.error(f"Error in /models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/add")
def memory_add(request: MemoryAddRequest, authorization: Optional[str] = Header(None)):
    """Add item to memory"""
    verify_token(authorization)
    
    try:
        from godman_ai.memory.vector_store import VectorStore
        
        store = VectorStore()
        store.add(request.text, request.metadata or {})
        return {"success": True}
    except Exception as e:
        logger.error(f"Error in /memory/add: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search")
def memory_search(request: MemorySearchRequest):
    """Search memory"""
    try:
        from godman_ai.memory.vector_store import VectorStore
        
        store = VectorStore()
        results = store.search(request.query, top_k=request.top_k)
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Error in /memory/search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Task scheduling endpoints
@app.post("/task")
def create_task(request: TaskCreateRequest, authorization: Optional[str] = Header(None)):
    """Create a scheduled task"""
    verify_token(authorization)
    
    try:
        from godman_ai.scheduler.task_manager import TaskManager
        
        manager = TaskManager()
        task_id = manager.create_task(
            task_input=request.task_input,
            schedule_type=request.schedule_type,
            schedule_value=request.schedule_value,
            priority=request.priority,
            metadata=request.metadata
        )
        
        task = manager.get_task(task_id)
        return {"success": True, "task_id": task_id, "task": task}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /task POST: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task")
def list_tasks(
    status: Optional[str] = None,
    schedule_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List scheduled tasks"""
    try:
        from godman_ai.scheduler.task_manager import TaskManager
        
        manager = TaskManager()
        tasks = manager.list_tasks(
            status=status,
            schedule_type=schedule_type,
            limit=limit,
            offset=offset
        )
        
        return {"success": True, "tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Error in /task GET: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task/{task_id}")
def get_task(task_id: int):
    """Get task details"""
    try:
        from godman_ai.scheduler.task_manager import TaskManager
        
        manager = TaskManager()
        task = manager.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return {"success": True, "task": task}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /task/{task_id} GET: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/task/{task_id}")
def update_task(task_id: int, request: TaskUpdateRequest, authorization: Optional[str] = Header(None)):
    """Update a scheduled task"""
    verify_token(authorization)
    
    try:
        from godman_ai.scheduler.task_manager import TaskManager
        
        manager = TaskManager()
        updated = manager.update_task(
            task_id=task_id,
            schedule_type=request.schedule_type,
            schedule_value=request.schedule_value,
            priority=request.priority,
            status=request.status,
            metadata=request.metadata
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        task = manager.get_task(task_id)
        return {"success": True, "task": task}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /task/{task_id} PUT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/task/{task_id}")
def delete_task(task_id: int, authorization: Optional[str] = Header(None)):
    """Delete/cancel a scheduled task"""
    verify_token(authorization)
    
    try:
        from godman_ai.scheduler.task_manager import TaskManager
        
        manager = TaskManager()
        deleted = manager.delete_task(task_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return {"success": True, "message": f"Task {task_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /task/{task_id} DELETE: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

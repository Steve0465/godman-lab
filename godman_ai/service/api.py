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

"""Health and introspection layer for GodmanAI OS Core."""

import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def system_health() -> Dict[str, Any]:
    """
    Get overall system health metrics.
    
    Returns:
        dict: Health status including workers, queue, scheduler, and failures
    """
    health = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {},
    }
    
    try:
        from godman_ai.os_core.state_manager import get_global_state
        state = get_global_state()
        
        # Check subsystem availability
        health["checks"]["settings"] = state.settings is not None
        health["checks"]["memory"] = state.memory is not None
        health["checks"]["queue"] = state.queue is not None
        health["checks"]["scheduler"] = state.scheduler is not None
        
        # Check queue depth
        if state.queue:
            try:
                queue_size = state.queue.size()
                health["checks"]["queue_depth"] = queue_size
                
                # Warn if queue is backed up
                if queue_size > 100:
                    health["status"] = "warning"
                    health["warnings"] = health.get("warnings", [])
                    health["warnings"].append(f"Queue depth high: {queue_size}")
            except Exception as e:
                logger.warning(f"Could not check queue depth: {e}")
        
        # Check failure rate
        stats = state.runtime_stats
        total = stats.get("total_tasks_executed", 0)
        failures = stats.get("total_failures", 0)
        
        if total > 0:
            failure_rate = (failures / total) * 100
            health["checks"]["failure_rate"] = f"{failure_rate:.1f}%"
            
            # Warn if failure rate is high
            if failure_rate > 10:
                health["status"] = "warning"
                health["warnings"] = health.get("warnings", [])
                health["warnings"].append(f"High failure rate: {failure_rate:.1f}%")
        
        # Check scheduler next run
        if state.scheduler:
            try:
                # TODO: Implement scheduler.next_run() method
                health["checks"]["scheduler_active"] = True
            except Exception as e:
                logger.warning(f"Could not check scheduler: {e}")
        
        # Check model availability
        from godman_ai.os_core.model_router import ModelRouter
        router = ModelRouter()
        available_models = router.list_available_models()
        health["checks"]["available_models"] = sum(1 for v in available_models.values() if v)
        
        if not any(available_models.values()):
            health["status"] = "degraded"
            health["warnings"] = health.get("warnings", [])
            health["warnings"].append("No AI models available")
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        health["status"] = "error"
        health["error"] = str(e)
    
    return health


def tool_stats() -> Dict[str, Any]:
    """
    Get statistics about tool usage and performance.
    
    Returns:
        dict: Tool usage frequencies and metrics
    """
    try:
        from godman_ai.os_core.state_manager import get_global_state
        state = get_global_state()
        
        tool_usage = state.runtime_stats.get("tool_usage_frequencies", {})
        
        # Sort by usage count
        sorted_tools = sorted(
            tool_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "total_tools_used": len(tool_usage),
            "total_invocations": sum(tool_usage.values()),
            "top_tools": dict(sorted_tools[:10]),
            "all_tools": dict(sorted_tools),
        }
    except Exception as e:
        logger.error(f"Error getting tool stats: {e}")
        return {"error": str(e)}


def model_stats() -> Dict[str, Any]:
    """
    Get statistics about model usage and availability.
    
    Returns:
        dict: Model availability and usage metrics
    """
    try:
        from godman_ai.os_core.state_manager import get_global_state
        from godman_ai.os_core.model_router import ModelRouter
        
        state = get_global_state()
        router = ModelRouter()
        
        available_models = router.list_available_models()
        active_models = state.active_models
        
        return {
            "available_models": available_models,
            "active_models": active_models,
            "model_preferences": router.model_prefs,
            "total_available": sum(1 for v in available_models.values() if v),
        }
    except Exception as e:
        logger.error(f"Error getting model stats: {e}")
        return {"error": str(e)}


def agent_stats() -> Dict[str, Any]:
    """
    Get statistics about agent performance.
    
    Returns:
        dict: Agent execution metrics
    """
    try:
        from godman_ai.os_core.state_manager import get_global_state
        state = get_global_state()
        
        stats = state.runtime_stats
        
        total = stats.get("total_tasks_executed", 0)
        failures = stats.get("total_failures", 0)
        avg_time = stats.get("average_execution_time", 0.0)
        
        success_rate = 0.0
        if total > 0:
            success_rate = ((total - failures) / total) * 100
        
        return {
            "total_tasks_executed": total,
            "total_failures": failures,
            "success_rate": f"{success_rate:.1f}%",
            "average_execution_time": f"{avg_time:.2f}s",
            "uptime": time.time() - stats.get("started_at", time.time()),
        }
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        return {"error": str(e)}


def memory_stats() -> Dict[str, Any]:
    """
    Get statistics about memory usage.
    
    Returns:
        dict: Memory size and vector count
    """
    try:
        from godman_ai.os_core.state_manager import get_global_state
        state = get_global_state()
        
        stats = {
            "episodic_memory_enabled": False,
            "working_memory_enabled": False,
            "vector_store_enabled": False,
        }
        
        if state.memory:
            if "episodic" in state.memory:
                stats["episodic_memory_enabled"] = True
                # TODO: Get episode count
            
            if "working" in state.memory:
                stats["working_memory_enabled"] = True
                # TODO: Get working memory size
        
        return stats
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return {"error": str(e)}


def full_report() -> Dict[str, Any]:
    """
    Generate a comprehensive system report.
    
    Returns:
        dict: Complete system status and statistics
    """
    return {
        "system_health": system_health(),
        "tool_stats": tool_stats(),
        "model_stats": model_stats(),
        "agent_stats": agent_stats(),
        "memory_stats": memory_stats(),
    }

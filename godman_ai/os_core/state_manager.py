"""Global state manager for GodmanAI OS Core."""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict


class GlobalState:
    """
    Manages global runtime state for GodmanAI.
    
    Tracks settings, memory, queue, scheduler, active models, and runtime statistics.
    Stores state files under .godman/state/runtime/
    """

    def __init__(self):
        self.state_dir = Path.home() / ".godman" / "state" / "runtime"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.settings = None
        self.memory = None
        self.queue = None
        self.scheduler = None
        self.active_models = []
        
        self.runtime_stats = {
            "total_tasks_executed": 0,
            "total_failures": 0,
            "average_execution_time": 0.0,
            "tool_usage_frequencies": {},
            "started_at": time.time(),
        }
        
        self._load_state()

    def _load_state(self):
        """Load persisted state from disk if available."""
        state_file = self.state_dir / "state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)
                    self.runtime_stats.update(data.get("runtime_stats", {}))
            except Exception as e:
                print(f"Warning: Could not load state: {e}")

    def _save_state(self):
        """Persist runtime state to disk."""
        state_file = self.state_dir / "state.json"
        try:
            with open(state_file, "w") as f:
                json.dump({
                    "runtime_stats": self.runtime_stats,
                    "active_models": self.active_models,
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")

    def initialize(self):
        """Initialize all subsystems lazily."""
        # Lazy load settings
        if self.settings is None:
            try:
                from godman_ai.config.loader import load_settings
                self.settings = load_settings()
            except Exception as e:
                print(f"Warning: Could not load settings: {e}")
        
        # Lazy load memory
        if self.memory is None:
            try:
                from godman_ai.memory.episodic_memory import EpisodicMemory
                from godman_ai.memory.working_memory import WorkingMemory
                self.memory = {
                    "episodic": EpisodicMemory(),
                    "working": WorkingMemory(),
                }
            except Exception as e:
                print(f"Warning: Could not load memory: {e}")
        
        # Lazy load queue
        if self.queue is None:
            try:
                from godman_ai.queue.job_queue import JobQueue
                self.queue = JobQueue()
            except Exception as e:
                print(f"Warning: Could not load queue: {e}")
        
        # Lazy load scheduler
        if self.scheduler is None:
            try:
                from godman_ai.scheduler.scheduler import Scheduler
                self.scheduler = Scheduler()
            except Exception as e:
                print(f"Warning: Could not load scheduler: {e}")

    def snapshot(self) -> Dict[str, Any]:
        """
        Returns a snapshot of the current global state.
        
        Returns:
            dict: Complete state snapshot including settings, stats, and subsystems
        """
        uptime = time.time() - self.runtime_stats.get("started_at", time.time())
        
        return {
            "uptime_seconds": uptime,
            "settings_loaded": self.settings is not None,
            "memory_loaded": self.memory is not None,
            "queue_loaded": self.queue is not None,
            "scheduler_loaded": self.scheduler is not None,
            "active_models": self.active_models,
            "runtime_stats": self.runtime_stats.copy(),
        }

    def update_tool_usage(self, tool_name: str):
        """
        Track tool usage frequency.
        
        Args:
            tool_name: Name of the tool that was used
        """
        freq = self.runtime_stats["tool_usage_frequencies"]
        freq[tool_name] = freq.get(tool_name, 0) + 1
        self._save_state()

    def record_task_execution(self, success: bool, execution_time: float):
        """
        Record task execution metrics.
        
        Args:
            success: Whether the task succeeded
            execution_time: Time taken to execute in seconds
        """
        self.runtime_stats["total_tasks_executed"] += 1
        
        if not success:
            self.runtime_stats["total_failures"] += 1
        
        # Update rolling average execution time
        current_avg = self.runtime_stats["average_execution_time"]
        total_tasks = self.runtime_stats["total_tasks_executed"]
        new_avg = ((current_avg * (total_tasks - 1)) + execution_time) / total_tasks
        self.runtime_stats["average_execution_time"] = new_avg
        
        self._save_state()

    def register_model(self, model_name: str):
        """
        Register an active model.
        
        Args:
            model_name: Name/identifier of the model
        """
        if model_name not in self.active_models:
            self.active_models.append(model_name)
            self._save_state()


# Global singleton instance
_global_state = None


def get_global_state() -> GlobalState:
    """Get or create the global state singleton."""
    global _global_state
    if _global_state is None:
        _global_state = GlobalState()
        _global_state.initialize()
    return _global_state

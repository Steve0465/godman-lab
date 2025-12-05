"""Godman AI - Intelligent automation agent for personal productivity."""
__version__ = "0.1.0"
__author__ = "Stephen Godman"

from .engine import AgentEngine, BaseTool, BaseWorkflow
from .orchestrator import Orchestrator
from .agents import AgentLoop, PlannerAgent, ExecutorAgent, ReviewerAgent

__all__ = [
    'AgentEngine',
    'BaseTool',
    'BaseWorkflow',
    'Orchestrator',
    'AgentLoop',
    'PlannerAgent',
    'ExecutorAgent',
    'ReviewerAgent'
]

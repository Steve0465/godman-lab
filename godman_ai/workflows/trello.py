"""Trello workflow wrappers."""

from pathlib import Path
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml

BASE = Path(__file__).resolve().parents[2] / "workflows"


def load_trello_daily():
    return load_workflow_from_yaml(BASE / "trello_daily_planner.dsl.yaml")


def load_trello_job_summary():
    return load_workflow_from_yaml(BASE / "trello_job_deep_summarize.dsl.yaml")

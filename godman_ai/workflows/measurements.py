"""Measurement workflow wrappers."""

from pathlib import Path
from typing import Optional, Dict, Any

from godman_ai.workflows.dsl_loader import load_workflow_from_yaml

BASE = Path(__file__).resolve().parents[2] / "workflows"


def run_safety_cover_review(input_path: str, options: Optional[Dict[str, Any]] = None):
    wf = load_workflow_from_yaml(BASE / "safety_cover_measurement_review.dsl.yaml")
    return wf


def run_liner_measurement_review(input_path: str, options: Optional[Dict[str, Any]] = None):
    wf = load_workflow_from_yaml(BASE / "liner_measurement_review.dsl.yaml")
    return wf


def load_measurement_full():
    return load_workflow_from_yaml(BASE / "measurement_full_analysis.dsl.yaml")


def load_trello_measurement_auto():
    return load_workflow_from_yaml(BASE / "trello_measurement_auto.dsl.yaml")


def load_cover_fit_estimator():
    return load_workflow_from_yaml(BASE / "cover_fit_estimator.dsl.yaml")

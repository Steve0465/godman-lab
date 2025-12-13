"""Drive automation workflow wrappers."""

from pathlib import Path
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml

BASE = Path(__file__).resolve().parents[2] / "workflows"


def load_drive_auto_ingest():
    return load_workflow_from_yaml(BASE / "drive_auto_ingest.dsl.yaml")


def load_drive_cleanup():
    return load_workflow_from_yaml(BASE / "drive_cleanup.dsl.yaml")


def load_drive_crosslink():
    return load_workflow_from_yaml(BASE / "drive_crosslink_trello.dsl.yaml")

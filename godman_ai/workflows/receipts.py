"""Receipt workflows wrappers."""

from pathlib import Path
from godman_ai.workflows.dsl_loader import load_workflow_from_yaml

BASE = Path(__file__).resolve().parents[2] / "workflows"


def load_receipt_full():
    return load_workflow_from_yaml(BASE / "workflow_receipt_full.dsl.yaml")


def load_receipt_monthly():
    return load_workflow_from_yaml(BASE / "workflow_receipt_monthly_aggregate.dsl.yaml")

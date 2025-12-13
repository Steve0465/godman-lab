import os
import pathlib
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("GODMAN_LOG_DIR", str(REPO_ROOT / "logs"))
os.environ.setdefault("HOME", str(REPO_ROOT.parent))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def repo_root_workdir(monkeypatch):
    """Ensure tests run from repository root and imports work."""
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("GODMAN_LOG_DIR", str(REPO_ROOT / "logs"))
    monkeypatch.setenv("HOME", str(REPO_ROOT.parent))
    monkeypatch.setattr(Path, "home", staticmethod(lambda: REPO_ROOT.parent))
    monkeypatch.setattr(pathlib.PosixPath, "home", classmethod(lambda cls: REPO_ROOT.parent))

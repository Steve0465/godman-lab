"""Mock Google Drive skill implementations for offline workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


def drive_upload(path: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
    target = folder_id or "root"
    name = Path(path).name
    return {"status": "uploaded", "file": name, "folder": target}


def drive_download(file_id: str, dest: str) -> Dict[str, Any]:
    return {"status": "downloaded", "file_id": file_id, "dest": dest}


def drive_search(query: str) -> Dict[str, Any]:
    return {"query": query, "results": []}


def drive_move(file_id: str, folder_id: str) -> Dict[str, Any]:
    return {"status": "moved", "file_id": file_id, "folder": folder_id}


def drive_copy(file_id: str, folder_id: str) -> Dict[str, Any]:
    return {"status": "copied", "file_id": file_id, "folder": folder_id}


def drive_share(file_id: str, email: str, role: str = "reader") -> Dict[str, Any]:
    return {"status": "shared", "file_id": file_id, "email": email, "role": role}

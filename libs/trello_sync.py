from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any

from .trello_client import TrelloClient

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    snapshot_path: Path
    actions_path: Path
    counts: Dict[str, int]
    latest_pointer: Path


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def sync_board(board_id: str, out_dir: str, since_days: int = 180) -> Dict[str, Any]:
    """Sync a board snapshot and actions to disk.

    Produces files under data/trello/<board_id>/:
      - snapshot_YYYYMMDD.json
      - actions_YYYYMMDD.json
      - latest.json pointer with metadata
    """
    base = Path(out_dir) / "trello" / board_id
    _ensure_dir(base)

    today_tag = datetime.now().strftime("%Y%m%d")
    snapshot_path = base / f"snapshot_{today_tag}.json"
    actions_path = base / f"actions_{today_tag}.json"
    latest_pointer = base / "latest.json"

    # Avoid overwrite if already exists
    if snapshot_path.exists() and actions_path.exists():
        logger.info("Snapshot already exists for today; returning existing paths")
        # Read counts if available
        counts = {"cards": 0, "lists": 0, "members": 0, "actions": 0}
        try:
            snap = json.loads(snapshot_path.read_text())
            counts.update({
                "cards": len(snap.get("cards", [])),
                "lists": len(snap.get("lists", [])),
                "members": len(snap.get("members", [])),
            })
        except Exception:
            pass
        try:
            acts = json.loads(actions_path.read_text())
            counts["actions"] = len(acts)
        except Exception:
            pass
        return {
            "snapshot_path": str(snapshot_path),
            "actions_path": str(actions_path),
            "counts": counts,
            "latest_pointer": str(latest_pointer),
        }

    # Build client from environment
    api_key = os.environ.get("TRELLO_API_KEY")
    token = os.environ.get("TRELLO_TOKEN")
    if not api_key or not token:
        raise RuntimeError("Missing TRELLO_API_KEY or TRELLO_TOKEN in environment")

    client = TrelloClient(api_key=api_key, token=token)

    # Fetch snapshot
    snapshot = client.get_board_snapshot(board_id)

    # Fetch actions since
    since_ts = datetime.now(timezone.utc) - timedelta(days=since_days)
    since_iso = _iso(since_ts)
    filters = "updateCard:idList,createCard,moveCardFromBoard,moveCardToBoard,updateCard:closed"
    actions = client.get_board_actions(board_id, since_iso=since_iso, filters=filters, limit=1000)

    # Write files
    snapshot_path.write_text(json.dumps(snapshot, indent=2))
    actions_path.write_text(json.dumps(actions, indent=2))

    # Latest pointer and symlinks
    meta = {
        "board_id": board_id,
        "generated_at": _iso(datetime.now(timezone.utc)),
        "snapshot": snapshot_path.name,
        "actions": actions_path.name,
        "counts": {
            "cards": len(snapshot.get("cards", [])),
            "lists": len(snapshot.get("lists", [])),
            "members": len(snapshot.get("members", [])),
            "actions": len(actions),
        },
    }
    latest_pointer.write_text(json.dumps(meta, indent=2))

    # Create/refresh convenience symlinks if supported
    try:
        snap_link = base / "snapshot_latest.json"
        act_link = base / "actions_latest.json"
        if snap_link.exists() or snap_link.is_symlink():
            snap_link.unlink()
        if act_link.exists() or act_link.is_symlink():
            act_link.unlink()
        snap_link.symlink_to(snapshot_path.name)
        act_link.symlink_to(actions_path.name)
    except Exception:
        # Symlink may not be supported; latest.json is sufficient
        pass

    return {
        "snapshot_path": str(snapshot_path),
        "actions_path": str(actions_path),
        "counts": meta["counts"],
        "latest_pointer": str(latest_pointer),
    }

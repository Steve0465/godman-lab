import csv
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

from libs.tool_runner import tool
from godman_ai.tools.trello_workorders import trello_pull_workorders


@tool(
    name="trello_export_workorders_csv",
    description="Export normalized Trello workorders to a CSV file (read-only). Args: board (or 'all'), include_closed, out_path (optional)",
)
def trello_export_workorders_csv(
    board: str = "all",
    include_closed: bool = False,
    out_path: str | None = None,
) -> Dict[str, Any]:
    result = trello_pull_workorders(board=board, include_closed=include_closed)
    workorders = result["workorders"]

    exports_dir = Path("exports")
    exports_dir.mkdir(parents=True, exist_ok=True)

    if out_path:
        out_file = Path(out_path)
        if not out_file.parent.exists():
            out_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = exports_dir / f"workorders_{board}_{stamp}.csv"

    fieldnames = [
        "board_key",
        "list_name",
        "customer",
        "city",
        "job_summary",
        "card_name_raw",
        "card_url",
        "due",
        "due_complete",
        "date_last_activity",
        "date_hint",
        "labels",
        "attachments_count",
    ]

    with out_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for wo in workorders:
            writer.writerow({
                "board_key": wo.get("board_key"),
                "list_name": wo.get("list_name"),
                "customer": wo.get("customer"),
                "city": wo.get("city"),
                "job_summary": wo.get("job_summary"),
                "card_name_raw": wo.get("card_name_raw"),
                "card_url": wo.get("card_url"),
                "due": wo.get("due"),
                "due_complete": wo.get("due_complete"),
                "date_last_activity": wo.get("date_last_activity"),
                "date_hint": wo.get("date_hint"),
                "labels": "|".join(wo.get("labels") or []),
                "attachments_count": wo.get("attachments_count", 0),
            })

    return {
        "status": "ok",
        "board": board,
        "include_closed": include_closed,
        "count": len(workorders),
        "csv_path": str(out_file),
    }


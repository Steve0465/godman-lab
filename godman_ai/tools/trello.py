"""
ToolRunner Trello tools (read-only).
"""

from typing import Any, Dict
from libs.tool_runner import tool
from godman_ai.services.trello_client import get_cards


@tool(
    name="trello_list_cards",
    description="List cards from a Trello board and list (read-only). Args: board, list",
)
def trello_list_cards(board: str, list: str) -> Dict[str, Any]:
    cards = get_cards(board, list)
    return {
        "board": board,
        "list": list,
        "count": len(cards),
        "cards": [{"id": c["id"], "name": c["name"], "url": c["url"]} for c in cards],
    }


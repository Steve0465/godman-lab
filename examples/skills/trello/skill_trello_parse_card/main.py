import asyncio
from typing import Dict


async def run(card: Dict[str, object]) -> Dict[str, object]:
    await asyncio.sleep(0)
    return {
        "title": card.get("name", ""),
        "description": card.get("desc", ""),
        "checklists": card.get("checklists", []),
    }

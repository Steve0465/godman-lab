import asyncio
from typing import Dict


async def run(board_id: str) -> Dict[str, object]:
    await asyncio.sleep(0)
    return {"board": {"id": board_id, "cards": [{"id": "c1", "name": "Fix roof", "desc": "address 123 main, duration 2h"}]}}

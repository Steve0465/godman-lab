import asyncio
from typing import Dict


ROUTES = {
    "receipt": "Receipts/Unsorted",
    "tax": "Tax/Current",
    "general": "Inbox",
}


async def run(classification: str) -> Dict[str, str]:
    await asyncio.sleep(0)
    return {"route": ROUTES.get(classification, "Inbox")}

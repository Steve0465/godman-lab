import asyncio
from typing import Dict


async def run(metadata: Dict[str, object]) -> Dict[str, bool]:
    await asyncio.sleep(0)
    name = str(metadata.get("name", ""))
    duplicate = name.endswith("_dup")
    return {"duplicate": duplicate}

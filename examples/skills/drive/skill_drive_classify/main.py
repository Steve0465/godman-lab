import asyncio
from typing import Dict


async def run(metadata: Dict[str, object]) -> Dict[str, str]:
    await asyncio.sleep(0)
    name = str(metadata.get("name", "")).lower()
    if "receipt" in name:
        cls = "receipt"
    elif "tax" in name:
        cls = "tax"
    else:
        cls = "general"
    return {"classification": cls}

import asyncio
from typing import Dict, List


MATERIAL_RULES = {
    "Roofing": ["shingles", "nails"],
    "Painting": ["paint", "brushes"],
    "General": ["gloves"],
}


async def run(job_type: str, description: str) -> Dict[str, List[str]]:
    await asyncio.sleep(0)
    materials = MATERIAL_RULES.get(job_type, ["gloves"])
    return {"materials": materials}

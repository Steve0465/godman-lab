import asyncio
from typing import Dict


async def run(job_type: str, description: str) -> Dict[str, float]:
    await asyncio.sleep(0)
    base = 2.0
    if job_type == "Roofing":
        base = 6.0
    elif job_type == "Painting":
        base = 4.0
    return {"duration_hours": base}

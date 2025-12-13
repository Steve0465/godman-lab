import asyncio
from typing import Dict


async def run(title: str, description: str) -> Dict[str, str]:
    await asyncio.sleep(0)
    text = f"{title} {description}".lower()
    if "roof" in text:
        job_type = "Roofing"
    elif "paint" in text:
        job_type = "Painting"
    else:
        job_type = "General"
    return {"job_type": job_type}

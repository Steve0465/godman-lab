import asyncio

from examples.skills.drive.skill_drive_classify import main as classify_main
from examples.skills.drive.skill_drive_dedupe import main as dedupe_main
from examples.skills.drive.skill_drive_inspect import main as inspect_main
from examples.skills.drive.skill_drive_normalize import main as normalize_main
from examples.skills.drive.skill_drive_route import main as route_main
from examples.skills.drive.skill_drive_store import main as store_main


def test_drive_skill_flow():
    metadata = asyncio.run(inspect_main.run("receipt.pdf"))
    cls = asyncio.run(classify_main.run(metadata["metadata"]))
    norm = asyncio.run(normalize_main.run(metadata["metadata"]))
    route = asyncio.run(route_main.run(cls["classification"]))
    store = asyncio.run(store_main.run(norm["filename"], route["route"]))
    dup = asyncio.run(dedupe_main.run(metadata["metadata"]))
    assert cls["classification"] in {"receipt", "tax", "general"}
    assert norm["filename"].endswith(".pdf") or norm["filename"].endswith(".txt")
    assert store["stored"].startswith(route["route"])
    assert isinstance(dup["duplicate"], bool)

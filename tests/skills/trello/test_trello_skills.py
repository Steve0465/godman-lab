import asyncio

from examples.skills.trello.skill_job_classify import main as classify_main
from examples.skills.trello.skill_job_duration_estimator import main as duration_main
from examples.skills.trello.skill_job_material_estimator import main as material_main
from examples.skills.trello.skill_trello_fetch_board import main as fetch_main
from examples.skills.trello.skill_trello_parse_card import main as parse_main


def test_trello_skill_flow():
    board = asyncio.run(fetch_main.run("b1"))
    card = board["board"]["cards"][0]
    parsed = asyncio.run(parse_main.run(card))
    job = asyncio.run(classify_main.run(parsed["title"], parsed["description"]))
    materials = asyncio.run(material_main.run(job["job_type"], parsed["description"]))
    duration = asyncio.run(duration_main.run(job["job_type"], parsed["description"]))
    assert job["job_type"] in {"Roofing", "Painting", "General"}
    assert isinstance(materials["materials"], list)
    assert duration["duration_hours"] > 0

from pathlib import Path

import pytest

from godman_ai.skills.loader import SkillLoadError, load_all_skills, load_skill


def test_load_skill_manifest_and_handler():
    skill = load_skill(Path("examples/skills/text_analyzer"))
    assert skill.manifest["name"] == "text_analyzer"
    result = skill.handler("abc")
    assert result["summary"].startswith("length=")


def test_load_all_skills_collects_multiple():
    skills = load_all_skills("examples/skills")
    names = sorted([s.manifest["name"] for s in skills])
    assert "text_analyzer" in names
    assert "image_metadata_extractor" in names


def test_missing_manifest_raises(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    with pytest.raises(SkillLoadError):
        load_skill(skill_dir)

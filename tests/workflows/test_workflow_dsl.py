from pathlib import Path
import asyncio

from godman_ai.workflows.dsl_loader import load_workflow_from_yaml


def test_load_workflow_from_yaml_switch_and_when(tmp_path):
    wf_yaml = tmp_path / "wf.yaml"
    wf_yaml.write_text(
        "steps:\n"
        "  - name: set_flag\n"
        "    action: \"set:flag=true\"\n"
        "  - name: choose\n"
        "    switch: flag\n"
        "    cases:\n"
        "      true: \"set:result=yes\"\n"
        "      false: \"set:result=no\"\n"
    )
    wf = load_workflow_from_yaml(wf_yaml)
    ctx = asyncio.run(wf.run())
    assert ctx.get("result") == "yes"

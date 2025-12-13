# Skills Overview

Skills are packaged capabilities with a manifest and a Python entrypoint.

## Manifest (skill.yaml)
- `name`, `version`, `description` (required)
- `entrypoint`: `module:function`
- `inputs` / `outputs`: descriptive lists
- `permissions`: optional list
- `metadata`: optional extras (models/tools required)

## Loading
```python
from godman_ai.skills import load_skill, load_all_skills

skill = load_skill("examples/skills/text_analyzer")
skills = load_all_skills("examples/skills")
```

## Entrypoint
Entrypoints are regular Python callables. Example (`examples/skills/text_analyzer/main.py`):
```python
def analyze(text: str):
    return {"summary": f"length={len(text)}"}
```

## Safety
- Manifests are validated for required fields.
- Entrypoints are imported dynamically; ensure they are side-effect free.
- No network access is assumed; skills should operate locally.

# Installation

## From Source
```bash
python -m pip install --upgrade pip
pip install -e .
```

## Build Wheel
```bash
python -m pip install build
python -m build
pip install dist/godman_ai-1.0.0-py3-none-any.whl
```

## Requirements
- Python >= 3.12
- Optional: `pyyaml` for YAML-based manifests/DSLs

## Post-Install Check
```bash
python - <<'PY'
import godman_ai
print(godman_ai.__version__)
PY
```

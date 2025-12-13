# Model Interface

`BaseModelInterface` standardizes model invocation across local and future backends.

## Contract
- `name`: model identifier.
- `async generate(prompt: str, **kwargs) -> str`: returns generated text.
- `trace_model` decorator: wraps async generate to record duration.

## Local Adapter
`LocalModelHandle` provides a minimal adapter for local model names and delegates to `LLMEngine` for compatibility.

## Usage
```python
from godman_ai.models.base import BaseModelInterface, LocalModelHandle

model: BaseModelInterface = LocalModelHandle("godman-raw:latest")
text = model.generate_sync("hello")
```

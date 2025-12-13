from godman_ai.models.base import BaseModelInterface, LocalModelHandle, trace_model


def test_local_model_handle_exposes_name():
    model: BaseModelInterface = LocalModelHandle("godman-raw:latest")
    assert model.name == "godman-raw:latest"


def test_trace_model_decorator_adds_duration_field():
    @trace_model
    async def generate():
        return {"text": "ok"}

    import asyncio
    result = asyncio.run(generate())
    assert result["text"] == "ok"
    assert "_duration_ms" in result

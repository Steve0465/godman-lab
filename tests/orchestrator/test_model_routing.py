import pytest

from godman_ai.local_router import LocalModelRouter, TaskType, select_model


@pytest.fixture
def router():
    return LocalModelRouter()


def test_classify_and_select(router):
    task = router.classify_task("Can you explain why the sky is blue?")
    assert task == TaskType.REASONING
    model = router.select_model(query="Please write a python function")
    assert model == LocalModelRouter.MODEL_PHI4


def test_route_metadata(router):
    meta = router.route("Let's chat about godman preferences")
    assert meta["model"] == LocalModelRouter.MODEL_GODMAN
    assert meta["task_type"] == TaskType.CUSTOM.value
    assert 0 <= meta["confidence"] <= 1


def test_select_model_helper_accepts_strings():
    assert select_model(task_type="code").endswith("phi4-14b:latest")


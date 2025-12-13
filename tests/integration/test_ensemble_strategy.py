from godman_ai.agents import strategies


def test_ensemble_selects_best():
    models = ["m1", "m2"]
    result = strategies.ensemble_two_models("task", models)
    assert result["action"] == "ensemble_select"
    assert result["model"] in models

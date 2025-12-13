from godman_ai.plugins import load_plugins, list_plugins


def test_receipt_plugins_load():
    load_plugins("examples/plugins")
    plugins = list_plugins()
    assert isinstance(plugins, list)

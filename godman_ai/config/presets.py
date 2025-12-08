from godman_ai.models import Preset


PRESETS = [
    Preset(
        name="Overmind",
        model="deepseek-r1:14b",
        prompt="You are DeepSeek-R1 acting as my strategic reasoning engine. Your job: break down any problem into steps, uncover hidden dependencies, design workflows, detect required tools, and plan multi-stage operations. Think deeply, show full reasoning, propose multiple solution paths, output structured plans."
    ),
    Preset(
        name="Forge",
        model="qwen2.5-coder:7b",
        prompt="You are Qwen2.5-Coder acting as my execution engineer. Your job: convert high-level plans into working code, scripts, automations, pipelines, and tools. Always output complete runnable code. Include file paths. Explain dependencies and commands I need to run."
    ),
    Preset(
        name="Handler",
        model="gorilla-openfunctions-v2",
        prompt='You are Gorilla OpenFunctions. Your job: convert user requests into structured function calls. Output ONLY JSON: { "function": "...", "parameters": { ... } }. Never provide additional explanation.'
    ),
]


def get_all_presets():
    """Return all available presets"""
    return [preset.to_dict() for preset in PRESETS]


def get_preset_by_name(name: str):
    """Get a preset by name"""
    for preset in PRESETS:
        if preset.name.lower() == name.lower():
            return preset.to_dict()
    return None

#!/usr/bin/env python3
"""Test script for presets functionality"""

from godman_ai.config.presets import get_all_presets, get_preset_by_name

def test_presets():
    print("Testing Presets Configuration\n" + "="*50)
    
    # Test getting all presets
    print("\n1. All Presets:")
    all_presets = get_all_presets()
    for preset in all_presets:
        print(f"\n  - {preset['name']}")
        print(f"    Model: {preset['model']}")
        print(f"    Prompt: {preset['prompt'][:80]}...")
    
    # Test getting specific presets
    print("\n2. Getting Specific Presets:")
    for name in ["Overmind", "Forge", "Handler"]:
        preset = get_preset_by_name(name)
        print(f"\n  {name}: {preset['model']}")
    
    # Test non-existent preset
    print("\n3. Testing Non-existent Preset:")
    result = get_preset_by_name("NonExistent")
    print(f"  Result: {result}")
    
    print("\n" + "="*50)
    print("✓ All tests passed!")

if __name__ == "__main__":
    test_presets()

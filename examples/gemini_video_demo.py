#!/usr/bin/env python3
"""
Gemini Video Analysis Demo - Native video support with Google Gemini.

Shows how to:
- Analyze videos directly with Gemini
- Extract frames for analysis with any provider
- Pool inspection video processing
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from godman_ai.tools.vision import VisionAnalyzer, VisionError


def demo_gemini_video():
    """Demo: Analyze video natively with Gemini."""
    print("\n" + "=" * 60)
    print("DEMO 1: Native Video Analysis with Gemini")
    print("=" * 60)
    
    try:
        # Initialize Gemini analyzer
        analyzer = VisionAnalyzer(provider="gemini")
        
        print("\n✓ Gemini VisionAnalyzer initialized")
        print(f"  Model: {analyzer.model}")
        print("\nTo use video analysis:")
        print("""
# Analyze pool inspection video
result = analyzer.analyze_video(
    "pool_inspection.mp4",
    "Analyze this pool inspection video. Identify all equipment, "
    "note conditions, and highlight any issues."
)

print(result["content"])
print(f"Video duration: {result['video_duration']}s")
        """)
        
    except VisionError as e:
        print(f"\n⚠️  {e}")
        print("\nTo fix:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        print("\nGet key from: https://aistudio.google.com/")


def demo_frame_extraction():
    """Demo: Extract frames for analysis with any provider."""
    print("\n" + "=" * 60)
    print("DEMO 2: Frame Extraction (works with any provider)")
    print("=" * 60)
    
    print("\nExtract frames every 5 seconds and analyze:")
    print("""
analyzer = VisionAnalyzer(provider="openai")  # or claude, gemini

# Extract frames
frames = analyzer.extract_frames(
    "pool_video.mp4",
    interval_seconds=5,
    max_frames=10  # Limit to first 10 frames
)

print(f"Extracted {len(frames)} frames")

# Analyze each frame
for i, frame in enumerate(frames):
    result = analyzer.analyze(
        frame,
        "Describe the pool equipment visible in this frame"
    )
    print(f"Frame {i}: {result['content'][:100]}...")
    """)


def demo_pool_inspection_workflow():
    """Demo: Complete pool inspection workflow."""
    print("\n" + "=" * 60)
    print("DEMO 3: Pool Inspection Workflow")
    print("=" * 60)
    
    print("\nComplete workflow for pool inspection videos:")
    print("""
from godman_ai.tools.vision import VisionAnalyzer

analyzer = VisionAnalyzer(provider="gemini")

# Analyze full video
result = analyzer.analyze_video(
    "job_site_video.mp4",
    '''
    Analyze this pool service video:
    
    1. Identify all pool equipment (pumps, filters, heaters, cleaners)
    2. Note model numbers if visible
    3. Assess condition (new, good, worn, damaged)
    4. Identify any safety issues
    5. Recommend maintenance or replacements
    
    Return detailed report with timestamps.
    '''
)

# Parse results
print("=== INSPECTION REPORT ===")
print(result["content"])

# Save to file
with open("inspection_report.txt", "w") as f:
    f.write(result["content"])
    """)


def demo_comparison():
    """Demo: Compare providers."""
    print("\n" + "=" * 60)
    print("DEMO 4: Provider Comparison")
    print("=" * 60)
    
    print("\n📊 VIDEO SUPPORT BY PROVIDER:")
    print("-" * 60)
    print("\n✅ Gemini 1.5 Pro:")
    print("   • Native video support (up to 1 hour)")
    print("   • Analyzes entire video at once")
    print("   • Best for: Complete video analysis, timestamps")
    print("   • Cost: ~$0.002/sec (~$7.20/hour)")
    
    print("\n⚠️  OpenAI GPT-4V:")
    print("   • No native video support")
    print("   • Use frame extraction")
    print("   • Best for: Single images, high accuracy")
    
    print("\n⚠️  Claude 3:")
    print("   • No native video support")
    print("   • Use frame extraction")
    print("   • Best for: Cost-effective image analysis")


def demo_practical_example():
    """Demo: Practical pool part identification from video."""
    print("\n" + "=" * 60)
    print("DEMO 5: Practical Example - Part ID from Video")
    print("=" * 60)
    
    print("\nIdentify parts from walkthrough video:")
    print("""
analyzer = VisionAnalyzer(provider="gemini")

# Analyze equipment walkthrough video
result = analyzer.analyze_video(
    "equipment_room.mp4",
    '''
    This is a video walkthrough of a pool equipment room.
    
    For each piece of equipment visible:
    1. Identify the type (pump, filter, heater, etc.)
    2. Extract visible model/part numbers
    3. Note manufacturer
    4. Estimate age/condition
    
    Return as JSON list:
    [
        {
            "equipment_type": "pump",
            "manufacturer": "Hayward",
            "model": "Super Pump",
            "part_numbers": ["SPX1091Z2"],
            "condition": "good",
            "timestamp": "0:15"
        },
        ...
    ]
    '''
)

# Parse and save parts list
import json
parts = json.loads(result["content"])

for part in parts:
    print(f"{part['timestamp']}: {part['equipment_type']} - {part['model']}")
    """)


def main():
    """Run all demos."""
    print("=" * 60)
    print("GEMINI VIDEO ANALYSIS - DEMO")
    print("Native Video Support with Google Gemini")
    print("=" * 60)
    
    demo_gemini_video()
    demo_frame_extraction()
    demo_pool_inspection_workflow()
    demo_comparison()
    demo_practical_example()
    
    print("\n" + "=" * 60)
    print("READY TO USE!")
    print("=" * 60)
    print("\nQuick Start:")
    print("  1. Get API key: https://aistudio.google.com/")
    print("  2. Set key: export GEMINI_API_KEY='your-key'")
    print("  3. Install: pip install google-generativeai opencv-python")
    print("  4. Import: from godman_ai.tools import VisionAnalyzer")
    print("  5. Analyze: analyzer.analyze_video('video.mp4', 'prompt')")
    
    print("\n💰 Cost Estimate:")
    print("  • 5-minute video analysis: ~$0.60")
    print("  • 30-minute inspection: ~$3.60")
    print("  • 1-hour walkthrough: ~$7.20")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

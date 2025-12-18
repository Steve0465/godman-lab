#!/usr/bin/env python3
"""
Vision Analyzer Demo - GPT-4V and Claude integration examples.

Shows how to use the VisionAnalyzer for:
- Pool part identification
- Generic image analysis
- Receipt parsing
- Document OCR
"""

import asyncio
from pathlib import Path

from godman_ai.tools.vision import VisionAnalyzer, VisionError


def demo_pool_part_identification():
    """Demo: Identify a pool part from an image."""
    print("\n" + "=" * 60)
    print("DEMO 1: Pool Part Identification")
    print("=" * 60)
    
    try:
        # Initialize with OpenAI GPT-4V
        analyzer = VisionAnalyzer(provider="openai")
        
        print("\nAnalyzing pool part image...")
        print("(This will send the image to OpenAI)")
        
        # NOTE: Replace with actual pool part image path
        # result = analyzer.analyze_pool_part("path/to/pool_part.jpg")
        
        print("\n✓ To use this:")
        print("  1. Set OPENAI_API_KEY environment variable")
        print("  2. Replace image path with actual pool part photo")
        print("  3. Run: result = analyzer.analyze_pool_part('your_image.jpg')")
        print("\nExample result:")
        print({
            "part_number": "SPX1091Z2",
            "manufacturer": "Hayward",
            "description": "Super Pump Housing Assembly",
            "confidence": 0.95,
            "alternatives": [
                {"part_number": "SPX1091Z1", "confidence": 0.75}
            ],
            "equivalents": ["PEN-355331", "JAC-39310700"]
        })
        
    except VisionError as e:
        print(f"\n⚠️  {e}")
        print("\nTo fix:")
        print("  export OPENAI_API_KEY='your-api-key-here'")


def demo_claude_vision():
    """Demo: Use Claude 3 for vision analysis."""
    print("\n" + "=" * 60)
    print("DEMO 2: Claude 3 Vision")
    print("=" * 60)
    
    try:
        # Initialize with Claude
        analyzer = VisionAnalyzer(provider="claude")
        
        print("\nUsing Claude 3 for analysis...")
        print("(Claude 3 Opus - best accuracy)")
        
        print("\n✓ To use this:")
        print("  1. Set ANTHROPIC_API_KEY environment variable")
        print("  2. analyzer = VisionAnalyzer(provider='claude')")
        print("  3. result = analyzer.analyze_pool_part('image.jpg')")
        
    except VisionError as e:
        print(f"\n⚠️  {e}")
        print("\nTo fix:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")


def demo_generic_analysis():
    """Demo: Generic image analysis with custom prompt."""
    print("\n" + "=" * 60)
    print("DEMO 3: Generic Image Analysis")
    print("=" * 60)
    
    print("\nThe VisionAnalyzer works for ANY image analysis:")
    print("\n1. Receipt parsing:")
    print("""
    result = analyzer.analyze(
        'receipt.jpg',
        'Extract vendor, date, total amount, and all line items as JSON'
    )
    """)
    
    print("\n2. Job site documentation:")
    print("""
    result = analyzer.analyze(
        'installation.jpg',
        'Describe the pool equipment installation. Note any issues.'
    )
    """)
    
    print("\n3. Equipment diagnostics:")
    print("""
    result = analyzer.analyze(
        'broken_pump.jpg',
        'Identify visible damage or issues with this pool pump'
    )
    """)
    
    print("\n4. Inventory counting:")
    print("""
    result = analyzer.analyze(
        'warehouse.jpg',
        'Count and list all visible pool parts in this image'
    )
    """)


def demo_workflow_integration():
    """Demo: Using VisionAnalyzer with PartIdentifierWorkflow."""
    print("\n" + "=" * 60)
    print("DEMO 4: Workflow Integration")
    print("=" * 60)
    
    print("\nThe PartIdentifierWorkflow now uses VisionAnalyzer automatically!")
    print("""
    from godman_ai.workflows import PartIdentifierWorkflow
    
    workflow = PartIdentifierWorkflow()
    
    # This will use GPT-4V for real analysis!
    result = await workflow.identify_part(
        image_path=Path("pool_part.jpg"),
        card_id="trello_card_id"  # Optional
    )
    
    print(f"Part: {result['primary_match']['part_number']}")
    print(f"Confidence: {result['primary_match']['confidence']:.1%}")
    
    # Or use Claude instead:
    result = await workflow.identify_part(
        image_path=Path("pool_part.jpg"),
        vision_provider="claude"  # Use Claude instead of OpenAI
    )
    """)


def demo_cost_estimation():
    """Demo: Cost estimation for vision API usage."""
    print("\n" + "=" * 60)
    print("DEMO 5: Cost Estimation")
    print("=" * 60)
    
    print("\n💰 PRICING (approximate):")
    print("-" * 60)
    print("\nOpenAI GPT-4V:")
    print("  • Low detail: ~$0.01 per image")
    print("  • High detail: ~$0.03 per image")
    print("\nClaude 3:")
    print("  • Haiku: ~$0.004 per image (fastest, cheapest)")
    print("  • Sonnet: ~$0.012 per image (good balance)")
    print("  • Opus: ~$0.024 per image (best accuracy)")
    
    print("\n📊 EXAMPLE COSTS:")
    print("-" * 60)
    print("  10 parts/day × 30 days = 300 images/month")
    print("  GPT-4V: $3-9/month")
    print("  Claude Opus: $7/month")
    print("  Claude Sonnet: $3.60/month")
    
    print("\n✅ Totally worth it for time saved!")


def main():
    """Run all demos."""
    print("=" * 60)
    print("VISION ANALYZER - DEMO")
    print("Cloud Vision AI for Pool Parts & More")
    print("=" * 60)
    
    demo_pool_part_identification()
    demo_claude_vision()
    demo_generic_analysis()
    demo_workflow_integration()
    demo_cost_estimation()
    
    print("\n" + "=" * 60)
    print("READY TO USE!")
    print("=" * 60)
    print("\nQuick Start:")
    print("  1. Set API key: export OPENAI_API_KEY='your-key'")
    print("  2. Import: from godman_ai.tools import VisionAnalyzer")
    print("  3. Analyze: analyzer.analyze_pool_part('image.jpg')")
    print("\nOr use with workflow:")
    print("  workflow = PartIdentifierWorkflow()")
    print("  result = await workflow.identify_part(image_path=Path('part.jpg'))")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

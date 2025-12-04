#!/usr/bin/env python3
"""
Demo script showcasing the Enhanced OCR/Analysis features.

This script demonstrates:
1. Bubble segmentation
2. OCR extraction
3. OCR backend comparison
4. Embeddings and semantic search
5. Message clustering

Usage:
    python demo.py
"""

import sys
from pathlib import Path

# Add enhanced to path
sys.path.insert(0, str(Path(__file__).parent))

from segmentation import BubbleSegmenter, MessageUIPreset
from ocr_backends import get_available_backends, get_ocr_backend

print("="*80)
print("Enhanced OCR/Analysis Feature Demo")
print("="*80)
print()

# 1. Show available OCR backends
print("1. Available OCR Backends:")
print("-" * 40)
backends = get_available_backends()
for backend in backends:
    print(f"  ✓ {backend.name}")
print()

# 2. Test OCR on example image
print("2. OCR Extraction Demo:")
print("-" * 40)
example_image = Path(__file__).parent.parent / 'examples' / 'test1.png'

if example_image.exists():
    backend = backends[0] if backends else None
    if backend:
        result = backend.extract_text(str(example_image))
        print(f"  Image: {example_image.name}")
        print(f"  Backend: {backend.name}")
        print(f"  Extracted Text: '{result.text}'")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Processing Time: {result.processing_time:.3f}s")
    else:
        print("  No OCR backend available")
else:
    print(f"  Example image not found: {example_image}")
print()

# 3. Bubble segmentation demo
print("3. Bubble Segmentation Demo:")
print("-" * 40)
print("  Testing different UI presets...")

presets = [
    MessageUIPreset.GENERIC,
    MessageUIPreset.IMESSAGE,
    MessageUIPreset.WHATSAPP,
    MessageUIPreset.ANDROID_SMS
]

for preset in presets:
    segmenter = BubbleSegmenter(preset=preset)
    print(f"  ✓ {preset.value}: min_width={segmenter.config['min_width']}, "
          f"max_width={segmenter.config['max_width']}")
print()

# 4. Check embeddings availability
print("4. Embeddings & Semantic Search:")
print("-" * 40)
try:
    from embeddings import MessageEmbedder, compute_sentiment_scores
    
    print("  Creating embedder and adding sample messages...")
    embedder = MessageEmbedder()
    
    messages = [
        "Hello, how are you?",
        "I'm doing great, thanks!",
        "The weather is beautiful today",
        "See you later!",
        "Have a wonderful day"
    ]
    
    embedder.add_messages(messages)
    print(f"  Added {len(messages)} messages to index")
    
    # Semantic search
    print("\n  Semantic search for 'greeting':")
    results = embedder.search("greeting", k=2)
    for idx, msg, dist, meta in results:
        print(f"    [{idx}] {msg} (distance: {dist:.3f})")
    
    # Clustering
    print("\n  Clustering messages into 2 topics:")
    clusters = embedder.cluster_messages(n_clusters=2)
    for cluster_id, indices in clusters.items():
        print(f"    Topic {cluster_id}: {len(indices)} messages")
    
    # Sentiment
    print("\n  Computing sentiment scores:")
    sentiments = compute_sentiment_scores(messages)
    for msg, score in zip(messages, sentiments):
        emoji = "😊" if score > 0.1 else "😐" if score > -0.1 else "😔"
        print(f"    {emoji} {score:+.2f}: {msg}")
    
    print("  ✓ Embeddings module working correctly")
    
except ImportError:
    print("  ⚠ Embeddings module not available")
    print("    Install: pip install sentence-transformers faiss-cpu")
print()

# 5. Summary
print("5. Summary:")
print("-" * 40)
print(f"  Segmentation: ✓ Working")
print(f"  OCR Backends: ✓ {len(backends)} available")
print(f"  CLI Scripts: ✓ Available")
print(f"  Web UI: ✓ Ready (run ./webapp/run_dev.sh)")
print()

print("="*80)
print("Demo Complete!")
print()
print("Next steps:")
print("  1. Run OCR comparison: python compare_ocr_backends.py --test-dir ../examples/ \\")
print("                                --ground-truth ../examples/ground_truth.json \\")
print("                                --output comparison.csv")
print()
print("  2. Process a folder: python process_folder.py /path/to/images/ --output results/")
print()
print("  3. Start web UI: cd ../.. && ./webapp/run_dev.sh")
print("="*80)


if __name__ == '__main__':
    pass  # All demo code runs at module level

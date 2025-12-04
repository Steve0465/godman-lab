#!/usr/bin/env python3
"""
Process folder script for end-to-end OCR pipeline.

This script processes a folder of images through:
1. Bubble segmentation
2. OCR extraction
3. Embedding generation
4. Storage in database/index

Example usage:
    python process_folder.py input_folder/ --output results/ --preset imessage
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from segmentation import BubbleSegmenter, MessageUIPreset
from ocr_backends import get_ocr_backend, get_available_backends

# Try to import embeddings (optional dependency)
try:
    from embeddings import MessageEmbedder
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    MessageEmbedder = None


def process_folder(input_folder: str, output_folder: str, 
                   preset: str = 'generic',
                   ocr_backend: str = 'tesseract',
                   store_embeddings: bool = True) -> Dict[str, Any]:
    """
    Process a folder of screenshots through the full pipeline.
    
    Args:
        input_folder: Path to input images
        output_folder: Path for output results
        preset: Segmentation preset to use
        ocr_backend: OCR backend to use
        store_embeddings: Whether to compute and store embeddings
        
    Returns:
        Dictionary with processing results
    """
    # Create output directory
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    print(f"Initializing segmenter with preset: {preset}")
    preset_map = {
        'imessage': MessageUIPreset.IMESSAGE,
        'whatsapp': MessageUIPreset.WHATSAPP,
        'android_sms': MessageUIPreset.ANDROID_SMS,
        'generic': MessageUIPreset.GENERIC
    }
    segmenter = BubbleSegmenter(preset=preset_map.get(preset, MessageUIPreset.GENERIC))
    
    print(f"Initializing OCR backend: {ocr_backend}")
    backend = get_ocr_backend(ocr_backend)
    if backend is None:
        print(f"Warning: {ocr_backend} backend not available, trying alternatives...")
        available = get_available_backends()
        if not available:
            print("Error: No OCR backends available!")
            return {'error': 'No OCR backends available'}
        backend = available[0]
        print(f"Using {backend.name} instead")
    
    embedder = None
    if store_embeddings:
        if not EMBEDDINGS_AVAILABLE:
            print("Warning: Embeddings module not available. Install sentence-transformers and faiss-cpu.")
            print("Skipping embedding generation.")
        else:
            print("Initializing embedder...")
            embedder = MessageEmbedder(index_path=str(output_path / 'embeddings'))
    
    # Process images
    results = {
        'images_processed': 0,
        'total_bubbles': 0,
        'total_messages': 0,
        'images': []
    }
    
    input_path = Path(input_folder)
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    for img_file in sorted(input_path.iterdir()):
        if img_file.suffix.lower() not in image_extensions:
            continue
        
        print(f"\nProcessing {img_file.name}...")
        
        try:
            # Step 1: Segment bubbles
            bubbles = segmenter.segment_image(str(img_file))
            print(f"  Found {len(bubbles)} bubbles")
            
            # Step 2: OCR each bubble
            messages = []
            for i, bubble in enumerate(bubbles):
                # Save bubble image temporarily
                bubble_path = output_path / 'temp' / f"{img_file.stem}_bubble_{i}.png"
                bubble_path.parent.mkdir(exist_ok=True)
                bubble.save(str(bubble_path))
                
                # Run OCR
                ocr_result = backend.extract_text(str(bubble_path))
                
                message_data = {
                    'bubble_index': i,
                    'text': ocr_result.text,
                    'confidence': ocr_result.confidence,
                    'bbox': bubble.to_dict()
                }
                messages.append(message_data)
                
                # Step 3: Add to embeddings
                if embedder and ocr_result.text.strip():
                    metadata = {
                        'source_image': img_file.name,
                        'bubble_index': i,
                        'confidence': ocr_result.confidence
                    }
                    embedder.add_message(ocr_result.text, metadata)
            
            # Save results for this image
            img_result = {
                'image': img_file.name,
                'num_bubbles': len(bubbles),
                'messages': messages
            }
            
            result_file = output_path / f"{img_file.stem}_result.json"
            with open(result_file, 'w') as f:
                json.dump(img_result, f, indent=2)
            
            print(f"  Extracted {len([m for m in messages if m['text'].strip()])} messages")
            
            results['images_processed'] += 1
            results['total_bubbles'] += len(bubbles)
            results['total_messages'] += len([m for m in messages if m['text'].strip()])
            results['images'].append(img_result)
            
        except Exception as e:
            print(f"  Error: {e}")
            results['images'].append({
                'image': img_file.name,
                'error': str(e)
            })
    
    # Save embeddings
    if embedder:
        print("\nSaving embeddings...")
        embedder.save(str(output_path / 'embeddings'))
        stats = embedder.compute_statistics()
        print(f"  Total messages in index: {stats['num_messages']}")
    
    # Save overall results
    summary_file = output_path / 'processing_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("Processing Complete!")
    print(f"{'='*60}")
    print(f"Images processed: {results['images_processed']}")
    print(f"Total bubbles: {results['total_bubbles']}")
    print(f"Total messages: {results['total_messages']}")
    print(f"\nResults saved to: {output_folder}")
    
    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Process screenshots through segmentation -> OCR -> embeddings pipeline'
    )
    parser.add_argument('input_folder', help='Folder containing input screenshots')
    parser.add_argument('--output', '-o', required=True, help='Output folder for results')
    parser.add_argument('--preset', choices=['imessage', 'whatsapp', 'android_sms', 'generic'],
                       default='generic', help='Messaging UI preset for segmentation')
    parser.add_argument('--ocr', choices=['tesseract', 'google', 'aws'],
                       default='tesseract', help='OCR backend to use')
    parser.add_argument('--no-embeddings', action='store_true',
                       help='Skip embedding generation')
    
    args = parser.parse_args()
    
    process_folder(
        args.input_folder,
        args.output,
        preset=args.preset,
        ocr_backend=args.ocr,
        store_embeddings=not args.no_embeddings
    )


if __name__ == '__main__':
    main()

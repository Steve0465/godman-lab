"""
End-to-end processing pipeline for screenshots.

Runs: segmentation -> OCR -> embedding -> storage

Example usage:
    python process_folder.py screenshots/ output/ --preset imessage --backend tesseract
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List
import sys

from prototype.enhanced.segmentation import BubbleSegmenter, process_folder as segment_folder
from prototype.enhanced.ocr_backends import get_ocr_backend, get_available_backends
from prototype.enhanced.embeddings import MessageEmbeddings, compute_message_sentiment


def process_pipeline(
    input_folder: str,
    output_folder: str,
    preset: str = 'imessage',
    backend: str = 'tesseract',
    skip_embedding: bool = False
) -> Dict:
    """
    Run complete processing pipeline on a folder of screenshots.
    
    Args:
        input_folder: Path to screenshots
        output_folder: Path for output
        preset: Segmentation preset
        backend: OCR backend name
        skip_embedding: Skip embedding computation
        
    Returns:
        Dictionary with processing statistics
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("ENHANCED OCR/THREAD ANALYZER PIPELINE")
    print("=" * 60)
    
    # Step 1: Segmentation
    print("\n[1/4] Running bubble segmentation...")
    segment_output = output_path / 'segments'
    segment_stats = segment_folder(input_folder, str(segment_output), preset)
    
    print(f"  ✓ Segmented {segment_stats['total_bubbles']} bubbles from {segment_stats['processed']} images")
    
    # Step 2: OCR
    print(f"\n[2/4] Running OCR with {backend} backend...")
    
    try:
        ocr = get_ocr_backend(backend)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print(f"  Available backends: {', '.join(get_available_backends())}")
        return {'error': str(e)}
    
    # Process each segmented image
    messages = []
    ocr_stats = {
        'total': 0,
        'successful': 0,
        'avg_confidence': 0.0
    }
    
    for image_dir in segment_output.iterdir():
        if not image_dir.is_dir():
            continue
        
        # Load metadata
        metadata_file = image_dir / 'metadata.json'
        if not metadata_file.exists():
            continue
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # OCR each bubble
        for bubble in metadata['bubbles']:
            bubble_path = image_dir / bubble['filename']
            if not bubble_path.exists():
                continue
            
            try:
                result = ocr.extract_text(str(bubble_path))
                
                if result.text:
                    message = {
                        'id': f"{image_dir.name}_{bubble['index']}",
                        'text': result.text,
                        'source_image': metadata['source_image'],
                        'bubble_index': bubble['index'],
                        'confidence': result.confidence,
                        'bounding_box': {
                            'x': bubble['x'],
                            'y': bubble['y'],
                            'width': bubble['width'],
                            'height': bubble['height']
                        }
                    }
                    messages.append(message)
                    
                    ocr_stats['successful'] += 1
                    if result.confidence:
                        ocr_stats['avg_confidence'] += result.confidence
                
                ocr_stats['total'] += 1
                
            except Exception as e:
                print(f"  Warning: OCR failed for {bubble_path.name}: {e}")
    
    if ocr_stats['successful'] > 0:
        ocr_stats['avg_confidence'] /= ocr_stats['successful']
    
    print(f"  ✓ Extracted text from {ocr_stats['successful']}/{ocr_stats['total']} bubbles")
    print(f"  ✓ Average confidence: {ocr_stats['avg_confidence']:.2%}")
    
    # Save OCR results
    ocr_output = output_path / 'ocr_results.json'
    with open(ocr_output, 'w') as f:
        json.dump(messages, f, indent=2)
    
    print(f"  ✓ Saved to {ocr_output}")
    
    # Step 3: Embeddings
    if not skip_embedding and messages:
        print("\n[3/4] Computing embeddings...")
        
        try:
            embedder = MessageEmbeddings()
            embedder.add_messages(messages)
            
            # Save embeddings
            embeddings_file = output_path / 'embeddings.pkl'
            embedder.save(str(embeddings_file))
            
            # Compute clusters and topics
            if len(messages) >= 3:
                n_clusters = min(5, len(messages))
                topics = embedder.get_cluster_topics(n_clusters=n_clusters)
                
                print(f"  ✓ Computed {len(messages)} embeddings")
                print(f"  ✓ Identified {len(topics)} topic clusters")
                
                # Save topics
                topics_file = output_path / 'topics.json'
                with open(topics_file, 'w') as f:
                    json.dump(topics, f, indent=2)
            else:
                print(f"  ✓ Computed {len(messages)} embeddings (too few for clustering)")
        
        except ImportError as e:
            print(f"  ⚠ Skipping embeddings: {e}")
    else:
        print("\n[3/4] Skipping embeddings (disabled or no messages)")
    
    # Step 4: Sentiment analysis
    print("\n[4/4] Computing sentiment...")
    
    for msg in messages:
        sentiment = compute_message_sentiment(msg['text'])
        msg['sentiment'] = sentiment
    
    # Save final results
    final_output = output_path / 'processed_messages.json'
    with open(final_output, 'w') as f:
        json.dump({
            'messages': messages,
            'stats': {
                'segmentation': segment_stats,
                'ocr': ocr_stats,
                'total_messages': len(messages)
            }
        }, f, indent=2)
    
    print(f"  ✓ Saved final results to {final_output}")
    
    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total images processed: {segment_stats['processed']}")
    print(f"Total bubbles detected: {segment_stats['total_bubbles']}")
    print(f"Total messages extracted: {len(messages)}")
    print(f"Output directory: {output_folder}")
    print("=" * 60)
    
    return {
        'segmentation': segment_stats,
        'ocr': ocr_stats,
        'messages': len(messages)
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process screenshots through segmentation, OCR, and embedding pipeline'
    )
    parser.add_argument('input', help='Input folder with screenshots')
    parser.add_argument('output', help='Output folder for processed data')
    parser.add_argument(
        '--preset',
        default='imessage',
        choices=['imessage', 'whatsapp', 'android_sms'],
        help='Messaging platform preset for segmentation'
    )
    parser.add_argument(
        '--backend',
        default='tesseract',
        choices=['tesseract', 'google_vision', 'aws_textract'],
        help='OCR backend to use'
    )
    parser.add_argument(
        '--skip-embedding',
        action='store_true',
        help='Skip embedding computation'
    )
    
    args = parser.parse_args()
    
    try:
        result = process_pipeline(
            args.input,
            args.output,
            preset=args.preset,
            backend=args.backend,
            skip_embedding=args.skip_embedding
        )
        
        if 'error' in result:
            sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

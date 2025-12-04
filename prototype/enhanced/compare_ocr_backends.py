"""
OCR backend comparison tool.

Compares accuracy of different OCR backends on labeled test data.

Example usage:
    python compare_ocr_backends.py prototype/examples/ prototype/examples/labels.json --output comparison.json
"""

import argparse
import sys
from pathlib import Path

from prototype.enhanced.ocr_backends import compare_backends, get_available_backends


def main():
    parser = argparse.ArgumentParser(
        description='Compare OCR backend accuracy on labeled test images'
    )
    parser.add_argument(
        'images',
        help='Folder containing test images'
    )
    parser.add_argument(
        'labels',
        help='JSON file with ground truth labels'
    )
    parser.add_argument(
        '--output',
        default='comparison.json',
        help='Output file for comparison results (default: comparison.json)'
    )
    
    args = parser.parse_args()
    
    # Check if inputs exist
    images_path = Path(args.images)
    labels_path = Path(args.labels)
    
    if not images_path.exists():
        print(f"Error: Images folder not found: {args.images}")
        sys.exit(1)
    
    if not labels_path.exists():
        print(f"Error: Labels file not found: {args.labels}")
        sys.exit(1)
    
    # Check available backends
    available = get_available_backends()
    if not available:
        print("Error: No OCR backends available!")
        print("\nPlease install at least one backend:")
        print("  - Tesseract: pip install pytesseract")
        print("  - Google Vision: pip install google-cloud-vision (+ set GOOGLE_APPLICATION_CREDENTIALS)")
        print("  - AWS Textract: pip install boto3 (+ configure AWS credentials)")
        sys.exit(1)
    
    print("OCR Backend Comparison Tool")
    print("=" * 60)
    print(f"Images folder: {args.images}")
    print(f"Labels file: {args.labels}")
    print(f"Output file: {args.output}")
    print(f"Available backends: {', '.join(available)}")
    print("=" * 60)
    print()
    
    try:
        results = compare_backends(args.images, args.labels, args.output)
        
        # Print summary
        print("\n" + "=" * 60)
        print("COMPARISON SUMMARY")
        print("=" * 60)
        
        for backend_name, stats in results.get('backends', {}).items():
            print(f"\n{backend_name.upper()}:")
            print(f"  Images processed: {stats['successful']}/{stats['total_images']}")
            print(f"  Average confidence: {stats['avg_confidence']:.2%}")
            print(f"  Average F1 score: {stats['avg_f1']:.3f}")
            print(f"  Average WER: {stats['avg_wer']:.3f}")
            print(f"  Average processing time: {stats['avg_processing_time']:.3f}s")
        
        print("\n" + "=" * 60)
        print(f"✓ Full results saved to {args.output}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Comparison failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

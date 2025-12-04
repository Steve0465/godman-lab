#!/usr/bin/env python3
"""
Compare OCR backends script.

Runs accuracy comparison across available OCR backends and produces a report.

Example usage:
    python compare_ocr_backends.py --test-dir examples/ --ground-truth examples/ground_truth.json --output comparison.csv
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ocr_backends import OCRComparator

if __name__ == '__main__':
    from ocr_backends import main
    main()

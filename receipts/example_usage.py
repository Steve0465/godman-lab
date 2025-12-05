#!/usr/bin/env python3
"""
Example usage of the receipt processing system.

This script demonstrates how to use the receipt processing functions.
"""

import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from receipts.process_receipts import parse_receipt_text, run


def example_parse_text():
    """Example: Parse a receipt text string."""
    print("Example 1: Parse receipt text")
    print("=" * 60)
    
    receipt_text = """
    WHOLE FOODS MARKET
    123 Organic Ave
    
    Date: 03/20/2024
    
    Apples          $4.99
    Bread           $3.50
    Milk            $4.25
    
    Subtotal        $12.74
    Tax             $1.15
    Total           $13.89
    
    Visa ending 1234
    """
    
    result = parse_receipt_text(receipt_text)
    
    print("Parsed fields:")
    for field, value in result.items():
        print(f"  {field:15s}: {value}")
    print()


def example_process_receipts():
    """Example: Process all receipts in raw/ directory."""
    print("Example 2: Process all receipt images")
    print("=" * 60)
    print("This will process all images in receipts/raw/")
    print("Results will be saved to receipts/receipts_master.csv")
    print()
    
    # Process all receipts
    run()
    print()


def example_batch_parsing():
    """Example: Parse multiple receipt texts."""
    print("Example 3: Batch parse receipt texts")
    print("=" * 60)
    
    receipts = [
        {
            'name': 'Receipt 1',
            'text': 'TARGET\nDate: 01/15/2024\nTotal: $25.99\nCredit Card'
        },
        {
            'name': 'Receipt 2',
            'text': 'STARBUCKS\n2024-02-20\nTotal: $5.50\nCash'
        },
        {
            'name': 'Receipt 3',
            'text': 'SHELL GAS\nDate: Mar 10, 2024\nTotal: $45.00\nDebit Card'
        }
    ]
    
    for receipt in receipts:
        result = parse_receipt_text(receipt['text'])
        print(f"{receipt['name']}:")
        print(f"  Vendor: {result['vendor']}")
        print(f"  Date: {result['date']}")
        print(f"  Total: ${result['total']}")
        print(f"  Payment: {result['payment_method']}")
        print()


if __name__ == '__main__':
    # Run examples
    example_parse_text()
    example_process_receipts()
    example_batch_parsing()

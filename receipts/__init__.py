"""
Receipt Processing System

A system for processing receipt images using OCR and extracting structured data.
"""

from .process_receipts import parse_receipt_text, run

__all__ = ['parse_receipt_text', 'run']

#!/usr/bin/env python3
"""
Unit tests for receipt processing system.

Tests the parsing logic without requiring actual images.
"""

import unittest
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from receipts.process_receipts import (
    parse_receipt_text,
    _extract_date,
    _extract_vendor,
    _extract_amounts,
    _normalize_amount,
    _extract_payment_method,
)


class TestParseReceiptText(unittest.TestCase):
    """Test the main parse_receipt_text function."""
    
    def test_parse_complete_receipt(self):
        """Test parsing a complete receipt with all fields."""
        receipt_text = """
        TARGET STORE #1234
        123 Main Street
        Date: 01/15/2024
        
        Item 1          $10.99
        Item 2          $24.50
        
        Subtotal        $35.49
        Tax             $3.19
        Total           $38.68
        
        Credit Card ending in 4567
        """
        
        result = parse_receipt_text(receipt_text)
        
        self.assertEqual(result['date'], '2024-01-15')
        self.assertIn('TARGET', result['vendor'])
        self.assertEqual(result['subtotal'], '35.49')
        self.assertEqual(result['tax'], '3.19')
        self.assertEqual(result['total'], '38.68')
        self.assertEqual(result['payment_method'], 'credit')
    
    def test_parse_minimal_receipt(self):
        """Test parsing a receipt with minimal information."""
        receipt_text = """
        Corner Store
        Total $15.00
        """
        
        result = parse_receipt_text(receipt_text)
        
        self.assertEqual(result['vendor'], 'Corner Store')
        self.assertEqual(result['total'], '15.00')
        # Date might be None if not in text
        # Other fields might be None
    
    def test_parse_empty_text(self):
        """Test parsing empty text returns None values."""
        result = parse_receipt_text("")
        
        self.assertIsNone(result['date'])
        self.assertIsNone(result['vendor'])
        self.assertIsNone(result['subtotal'])
        self.assertIsNone(result['tax'])
        self.assertIsNone(result['total'])
        self.assertIsNone(result['payment_method'])
    
    def test_parse_none_text(self):
        """Test parsing None text returns None values."""
        result = parse_receipt_text(None)
        
        self.assertIsNone(result['date'])
        self.assertIsNone(result['vendor'])


class TestExtractDate(unittest.TestCase):
    """Test date extraction and normalization."""
    
    def test_extract_mmddyyyy_slash(self):
        """Test MM/DD/YYYY format."""
        text = "Date: 03/15/2024"
        result = _extract_date(text)
        self.assertEqual(result, '2024-03-15')
    
    def test_extract_mmddyyyy_dash(self):
        """Test MM-DD-YYYY format."""
        text = "Date: 03-15-2024"
        result = _extract_date(text)
        self.assertEqual(result, '2024-03-15')
    
    def test_extract_yyyymmdd(self):
        """Test YYYY-MM-DD format."""
        text = "Date: 2024-03-15"
        result = _extract_date(text)
        self.assertEqual(result, '2024-03-15')
    
    def test_extract_mmddyy(self):
        """Test MM/DD/YY format (2-digit year)."""
        text = "Date: 03/15/24"
        result = _extract_date(text)
        self.assertEqual(result, '2024-03-15')
    
    def test_extract_month_name(self):
        """Test month name format (Jan 15, 2024)."""
        text = "Date: Jan 15, 2024"
        result = _extract_date(text)
        self.assertEqual(result, '2024-01-15')
    
    def test_extract_month_name_full(self):
        """Test full month name format."""
        text = "Date: January 15, 2024"
        result = _extract_date(text)
        self.assertEqual(result, '2024-01-15')
    
    def test_extract_no_date(self):
        """Test when no date is present."""
        text = "No date here at all"
        result = _extract_date(text)
        self.assertIsNone(result)
    
    def test_extract_future_date_rejected(self):
        """Test that dates too far in future are rejected."""
        future_year = datetime.now().year + 5
        text = f"Date: 01/01/{future_year}"
        result = _extract_date(text)
        self.assertIsNone(result)
    
    def test_extract_old_date_rejected(self):
        """Test that dates before 2000 are rejected."""
        text = "Date: 01/01/1999"
        result = _extract_date(text)
        self.assertIsNone(result)


class TestExtractVendor(unittest.TestCase):
    """Test vendor name extraction."""
    
    def test_extract_simple_vendor(self):
        """Test extracting simple vendor name."""
        text = """
        WALMART
        Store #1234
        """
        result = _extract_vendor(text)
        self.assertEqual(result, 'WALMART')
    
    def test_extract_vendor_skip_keywords(self):
        """Test that common keywords are skipped."""
        text = """
        RECEIPT
        INVOICE
        TARGET STORE
        """
        result = _extract_vendor(text)
        self.assertEqual(result, 'TARGET STORE')
    
    def test_extract_vendor_skip_short(self):
        """Test that very short lines are skipped."""
        text = """
        AB
        TARGET STORE
        """
        result = _extract_vendor(text)
        self.assertEqual(result, 'TARGET STORE')
    
    def test_extract_vendor_skip_numeric(self):
        """Test that mostly numeric lines are skipped."""
        text = """
        123456789
        BEST BUY
        """
        result = _extract_vendor(text)
        self.assertEqual(result, 'BEST BUY')
    
    def test_extract_vendor_empty(self):
        """Test extracting from empty text."""
        text = ""
        result = _extract_vendor(text)
        self.assertIsNone(result)
    
    def test_extract_vendor_truncated(self):
        """Test that very long vendor names are truncated."""
        long_name = "A" * 150
        text = long_name
        result = _extract_vendor(text)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 100)


class TestExtractAmounts(unittest.TestCase):
    """Test monetary amount extraction."""
    
    def test_extract_all_amounts(self):
        """Test extracting subtotal, tax, and total."""
        text = """
        Subtotal    $50.00
        Tax         $4.50
        Total       $54.50
        """
        result = _extract_amounts(text)
        self.assertEqual(result['subtotal'], '50.00')
        self.assertEqual(result['tax'], '4.50')
        self.assertEqual(result['total'], '54.50')
    
    def test_extract_with_commas(self):
        """Test extracting amounts with comma separators."""
        text = """
        Subtotal    $1,234.56
        Tax         $123.45
        Total       $1,358.01
        """
        result = _extract_amounts(text)
        self.assertEqual(result['subtotal'], '1234.56')
        self.assertEqual(result['tax'], '123.45')
        self.assertEqual(result['total'], '1358.01')
    
    def test_extract_without_dollar_sign(self):
        """Test extracting amounts without dollar signs."""
        text = """
        Subtotal    25.00
        Tax         2.25
        Total       27.25
        """
        result = _extract_amounts(text)
        self.assertEqual(result['subtotal'], '25.00')
        self.assertEqual(result['tax'], '2.25')
        self.assertEqual(result['total'], '27.25')
    
    def test_extract_total_only(self):
        """Test extracting when only total is present."""
        text = """
        Total: $100.00
        """
        result = _extract_amounts(text)
        self.assertEqual(result['total'], '100.00')
        self.assertIsNone(result['subtotal'])
        self.assertIsNone(result['tax'])
    
    def test_extract_fallback_to_max(self):
        """Test fallback to largest amount when no total label."""
        text = """
        Item 1    $5.00
        Item 2    $10.00
        Item 3    $85.00
        """
        result = _extract_amounts(text)
        self.assertEqual(result['total'], '85.00')
    
    def test_extract_no_amounts(self):
        """Test when no amounts are present."""
        text = "No amounts here"
        result = _extract_amounts(text)
        self.assertIsNone(result['total'])
        self.assertIsNone(result['subtotal'])
        self.assertIsNone(result['tax'])


class TestNormalizeAmount(unittest.TestCase):
    """Test amount normalization."""
    
    def test_normalize_simple(self):
        """Test normalizing simple amount."""
        result = _normalize_amount("25.50")
        self.assertEqual(result, "25.50")
    
    def test_normalize_with_dollar_sign(self):
        """Test normalizing amount with dollar sign."""
        result = _normalize_amount("$25.50")
        self.assertEqual(result, "25.50")
    
    def test_normalize_with_commas(self):
        """Test normalizing amount with commas."""
        result = _normalize_amount("1,234.56")
        self.assertEqual(result, "1234.56")
    
    def test_normalize_euro(self):
        """Test normalizing amount with euro symbol."""
        result = _normalize_amount("€25.50")
        self.assertEqual(result, "25.50")
    
    def test_normalize_pound(self):
        """Test normalizing amount with pound symbol."""
        result = _normalize_amount("£25.50")
        self.assertEqual(result, "25.50")
    
    def test_normalize_integer(self):
        """Test normalizing integer amount."""
        result = _normalize_amount("25")
        self.assertEqual(result, "25.00")
    
    def test_normalize_invalid(self):
        """Test normalizing invalid amount."""
        result = _normalize_amount("invalid")
        self.assertIsNone(result)
    
    def test_normalize_none(self):
        """Test normalizing None."""
        result = _normalize_amount(None)
        self.assertIsNone(result)


class TestExtractPaymentMethod(unittest.TestCase):
    """Test payment method extraction."""
    
    def test_extract_credit_card(self):
        """Test extracting credit card payment."""
        text = "Paid with Credit Card"
        result = _extract_payment_method(text)
        self.assertEqual(result, 'credit')
    
    def test_extract_visa(self):
        """Test extracting Visa payment."""
        text = "Visa ending in 4567"
        result = _extract_payment_method(text)
        self.assertEqual(result, 'credit')
    
    def test_extract_debit(self):
        """Test extracting debit card payment."""
        text = "Debit Card"
        result = _extract_payment_method(text)
        self.assertEqual(result, 'debit')
    
    def test_extract_cash(self):
        """Test extracting cash payment."""
        text = "Paid in Cash"
        result = _extract_payment_method(text)
        self.assertEqual(result, 'cash')
    
    def test_extract_apple_pay(self):
        """Test extracting Apple Pay payment."""
        text = "Apple Pay transaction"
        result = _extract_payment_method(text)
        self.assertEqual(result, 'mobile')
    
    def test_extract_check(self):
        """Test extracting check payment."""
        text = "Payment by Check"
        result = _extract_payment_method(text)
        self.assertEqual(result, 'check')
    
    def test_extract_gift_card(self):
        """Test extracting gift card payment."""
        text = "Gift Card balance"
        result = _extract_payment_method(text)
        self.assertEqual(result, 'gift_card')
    
    def test_extract_no_payment_method(self):
        """Test when no payment method is found."""
        text = "No payment information"
        result = _extract_payment_method(text)
        self.assertIsNone(result)


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete receipt parsing scenarios."""
    
    def test_grocery_receipt(self):
        """Test parsing a typical grocery receipt."""
        receipt_text = """
        WHOLE FOODS MARKET
        123 Organic Ave
        
        Date: 12/25/2023
        
        Apples          $4.99
        Bread           $3.50
        Milk            $4.25
        
        Subtotal        $12.74
        Tax             $1.15
        Total           $13.89
        
        Visa ending 1234
        """
        
        result = parse_receipt_text(receipt_text)
        
        self.assertEqual(result['date'], '2023-12-25')
        self.assertIn('WHOLE FOODS', result['vendor'])
        self.assertEqual(result['subtotal'], '12.74')
        self.assertEqual(result['tax'], '1.15')
        self.assertEqual(result['total'], '13.89')
        self.assertEqual(result['payment_method'], 'credit')
    
    def test_restaurant_receipt(self):
        """Test parsing a restaurant receipt."""
        receipt_text = """
        THE PIZZA PLACE
        456 Main St
        
        03/20/2024
        
        Large Pizza     $18.99
        Soda            $2.50
        
        Subtotal        $21.49
        Tax             $1.93
        Total           $23.42
        
        Cash Payment
        """
        
        result = parse_receipt_text(receipt_text)
        
        self.assertEqual(result['date'], '2024-03-20')
        self.assertIn('PIZZA PLACE', result['vendor'])
        self.assertEqual(result['total'], '23.42')
        self.assertEqual(result['payment_method'], 'cash')
    
    def test_gas_station_receipt(self):
        """Test parsing a gas station receipt."""
        receipt_text = """
        SHELL STATION #4321
        
        Date: 2024-06-15
        
        Unleaded         $45.00
        
        Total            $45.00
        
        Debit Card ****5678
        """
        
        result = parse_receipt_text(receipt_text)
        
        self.assertEqual(result['date'], '2024-06-15')
        self.assertIn('SHELL', result['vendor'])
        self.assertEqual(result['total'], '45.00')
        self.assertEqual(result['payment_method'], 'debit')


if __name__ == '__main__':
    unittest.main()

import unittest
from process_receipts import parse_receipt_text, clean_currency

class TestReceiptParsing(unittest.TestCase):
    
    def test_clean_currency(self):
        self.assertEqual(clean_currency("$12.50"), 12.50)
        self.assertEqual(clean_currency("1,000.00"), 1000.00)
        self.assertEqual(clean_currency("invalid"), 0.0)

    def test_parse_simple_receipt(self):
        sample_text = """
        Walmart Supercenter
        12/01/2023
        
        Milk   $3.50
        Bread  $2.00
        
        Subtotal $5.50
        Tax      $0.50
        TOTAL    $6.00
        
        Paid with VISA ending in 1234
        """
        
        result = parse_receipt_text(sample_text)
        
        self.assertEqual(result['vendor'], "Walmart Supercenter")
        self.assertEqual(result['total'], 6.00)
        self.assertEqual(result['tax'], 0.50)
        self.assertEqual(result['payment_method'], "Card")

if __name__ == '__main__':
    unittest.main()

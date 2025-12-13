"""Tax document classifier module.

Classifies tax documents by inferring year and category from content analysis.

Trust Boundaries:
    - PDF text extraction may fail silently (malformed PDFs, encryption)
    - Extracted text may be incomplete or garbled
    - Year/category inference is heuristic, not guaranteed accurate
    - Confidence scores are subjective estimates, not statistical probabilities
    - All operations are wrapped in error handling to prevent exceptions

Classification Strategy:
    1. Extract text from first 2 pages of PDF using pdfplumber (no OCR)
    2. Normalize whitespace and clean text
    3. Scan for explicit tax year patterns ("Tax Year 2024", "For the year ended...")
    4. Fall back to dominant year frequency in content
    5. Reject future years beyond current_year + 1
    6. Look for known document type keywords (1099, W-2, etc.)
    7. Calculate confidence based on evidence strength

Confidence Scoring:
    Start at 0.0, add points for:
    - Explicit year phrase (e.g., "Tax Year 2024"): +0.5
    - Known document type (e.g., "Form 1099"): +0.3
    - Filename match: +0.1
    - Multiple corroborating signals increase confidence
    - Capped at 1.0

Year Inference:
    - Prefer explicit "Tax Year" language
    - Fall back to dominant year in date patterns
    - Reject years > current_year + 1

Category Inference:
    - 1099 → taxes
    - W-2 → taxes
    - Insurance → insurance
    - Statement / Ending Balance → bank_statements

Note: Currently only supports PDF files. Other formats return None results.
"""

from pathlib import Path
from typing import Optional
import re
from datetime import datetime

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from pydantic import BaseModel


class TaxClassificationResult(BaseModel):
    """Result of tax document classification.
    
    Attributes:
        path: Relative path to file
        inferred_year: Year extracted from document (None if not found)
        inferred_category: Category based on content (None if not determined)
        confidence: Confidence score 0.0-1.0 (higher = more confident)
        evidence: List of reasons supporting the classification
    """
    path: str
    inferred_year: Optional[int] = None
    inferred_category: Optional[str] = None
    confidence: float = 0.0
    evidence: list[str] = []


# Category keywords mapping (keyword -> category, confidence boost)
CATEGORY_KEYWORDS = {
    # Tax forms - highest priority
    'form 1099': ('taxes', 0.3),
    '1099': ('taxes', 0.3),
    'form w-2': ('taxes', 0.3),
    'w-2': ('taxes', 0.3),
    'form w2': ('taxes', 0.3),
    'w2': ('taxes', 0.3),
    'form 1040': ('taxes', 0.3),
    '1040': ('taxes', 0.3),
    'tax return': ('taxes', 0.3),
    'tax form': ('taxes', 0.3),
    'irs': ('taxes', 0.2),
    
    # Insurance
    'insurance': ('insurance', 0.3),
    'insurance policy': ('insurance', 0.3),
    'policy number': ('insurance', 0.2),
    'coverage': ('insurance', 0.2),
    'premium': ('insurance', 0.2),
    'insured': ('insurance', 0.2),
    
    # Bank statements
    'bank statement': ('bank_statements', 0.3),
    'statement period': ('bank_statements', 0.3),
    'ending balance': ('bank_statements', 0.3),
    'beginning balance': ('bank_statements', 0.3),
    'account summary': ('bank_statements', 0.2),
    'deposits': ('bank_statements', 0.2),
    'withdrawals': ('bank_statements', 0.2),
    'checking account': ('bank_statements', 0.2),
    'savings account': ('bank_statements', 0.2),
    
    # Statements (generic)
    'statement': ('statements', 0.2),
    'account statement': ('statements', 0.2),
    'monthly statement': ('statements', 0.2),
    'billing statement': ('statements', 0.2),
    
    # Receipts
    'receipt': ('receipts', 0.3),
    'purchase': ('receipts', 0.2),
    'total paid': ('receipts', 0.2),
    'payment received': ('receipts', 0.2),
    
    # Invoices
    'invoice': ('invoices', 0.3),
    'invoice number': ('invoices', 0.3),
    'invoice date': ('invoices', 0.2),
    'bill to': ('invoices', 0.2),
    'amount due': ('invoices', 0.2),
    
    # Contracts
    'contract': ('contracts', 0.3),
    'agreement': ('contracts', 0.3),
    'terms and conditions': ('contracts', 0.2),
    
    # Correspondence
    'dear': ('correspondence', 0.2),
    'sincerely': ('correspondence', 0.2),
    'letter': ('correspondence', 0.2),
    
    # Reports
    'annual report': ('reports', 0.3),
    'quarterly report': ('reports', 0.3),
    'financial report': ('reports', 0.3),
    'report': ('reports', 0.2),
}


class TaxClassifier:
    """Classifies tax documents by analyzing content.
    
    Uses text extraction and pattern matching to infer year and category
    from PDF documents. Provides confidence scores and evidence trail.
    
    Trust Boundaries:
    - PDF extraction may fail (returns None results with 0.0 confidence)
    - Text may be incomplete or inaccurate
    - Classification is heuristic, manual review recommended for low confidence
    - Never raises exceptions (all errors caught and logged in evidence)
    
    Limitations:
    - Currently only supports PDF files
    - No OCR support (scanned PDFs will have limited/no text)
    - Confidence scores are estimates, not statistical probabilities
    - May misclassify ambiguous documents
    """
    
    def __init__(self):
        """Initialize tax classifier.
        
        Checks for pdfplumber availability at initialization.
        """
        self.pdf_available = PDF_AVAILABLE
    
    def classify(self, path: Path) -> TaxClassificationResult:
        """Classify a tax document by analyzing its content.
        
        Attempts to extract text from PDF and infer year/category based on
        content analysis. Returns structured result with confidence and evidence.
        
        Trust Boundaries:
        - May return None values if extraction fails
        - May return low confidence if evidence is weak
        - Never raises exceptions (errors logged in evidence)
        
        Args:
            path: Path to document file to classify
            
        Returns:
            TaxClassificationResult with inferred metadata and evidence
            
        Examples:
            >>> classifier = TaxClassifier()
            >>> result = classifier.classify(Path("invoice.pdf"))
            >>> print(f"Year: {result.inferred_year}, Category: {result.inferred_category}")
            >>> print(f"Confidence: {result.confidence:.2f}")
            >>> for evidence in result.evidence:
            ...     print(f"  - {evidence}")
        """
        rel_path = str(path)
        
        # Check if file exists
        if not path.exists():
            return TaxClassificationResult(
                path=rel_path,
                confidence=0.0,
                evidence=["File does not exist"]
            )
        
        # Check if it's a PDF
        if path.suffix.lower() != '.pdf':
            return TaxClassificationResult(
                path=rel_path,
                confidence=0.0,
                evidence=[f"Unsupported file type: {path.suffix}"]
            )
        
        # Check if pdfplumber is available
        if not self.pdf_available:
            return TaxClassificationResult(
                path=rel_path,
                confidence=0.0,
                evidence=["pdfplumber not available (pip install pdfplumber)"]
            )
        
        # Extract text from PDF
        text = self._extract_pdf_text(path)
        
        if text is None:
            return TaxClassificationResult(
                path=rel_path,
                confidence=0.0,
                evidence=["Failed to extract text from PDF"]
            )
        
        if not text.strip():
            return TaxClassificationResult(
                path=rel_path,
                confidence=0.0,
                evidence=["PDF contains no extractable text (may be scanned/OCR needed)"]
            )
        
        # Classify based on content
        return self._classify_text(rel_path, text, path.name)
    
    def _extract_pdf_text(self, path: Path) -> Optional[str]:
        """Extract text from first 2 pages of PDF file.
        
        Uses pdfplumber to extract text. Normalizes whitespace.
        Catches all exceptions to prevent errors from propagating.
        
        Trust Boundaries:
        - May fail on encrypted PDFs
        - May fail on malformed PDFs
        - May return incomplete text
        - May return garbled text from complex layouts
        
        Args:
            path: Path to PDF file
            
        Returns:
            Extracted and normalized text or None if extraction failed
        """
        try:
            text_parts = []
            
            with pdfplumber.open(path) as pdf:
                # Extract from first 2 pages only
                for page in pdf.pages[:2]:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            if not text_parts:
                return None
            
            # Join and normalize whitespace
            text = "\n".join(text_parts)
            text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
            text = re.sub(r'\n+', '\n', text)  # Collapse newlines
            
            return text.strip()
            
        except Exception as e:
            # Catch all exceptions (encrypted, malformed, etc.)
            return None
    
    def _classify_text(self, rel_path: str, text: str, filename: str) -> TaxClassificationResult:
        """Classify document based on text content and filename.
        
        Confidence Scoring:
        - Start at 0.0
        - Explicit year phrase: +0.5
        - Known document type: +0.3
        - Filename match: +0.1
        - Multiple corroborating signals increase confidence
        
        Args:
            rel_path: Relative path for result
            text: Extracted and normalized text content
            filename: Original filename
            
        Returns:
            TaxClassificationResult with inferred metadata
        """
        evidence = []
        confidence = 0.0
        
        # Normalize text for analysis
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Infer year
        year, year_evidence, year_conf_boost = self._infer_year(text_lower, filename_lower)
        evidence.extend(year_evidence)
        confidence += year_conf_boost
        
        # Infer category
        category, category_evidence, cat_conf_boost = self._infer_category(text_lower, filename_lower)
        evidence.extend(category_evidence)
        confidence += cat_conf_boost
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        return TaxClassificationResult(
            path=rel_path,
            inferred_year=year,
            inferred_category=category,
            confidence=round(confidence, 2),
            evidence=evidence
        )
    
    def _infer_year(self, text_lower: str, filename_lower: str) -> tuple[Optional[int], list[str], float]:
        """Infer year from text content and filename.
        
        Detects patterns:
        - "Tax Year 2024" (explicit - highest priority)
        - "For the year ended December 31, 2023"
        - "2022 Form 1099"
        - Dominant year frequency in dates
        
        Rejects future years beyond current_year + 1.
        
        Args:
            text_lower: Lowercase text content
            filename_lower: Lowercase filename
            
        Returns:
            Tuple of (year, evidence_list, confidence_boost)
        """
        evidence = []
        confidence_boost = 0.0
        current_year = datetime.now().year
        max_allowed_year = current_year + 1
        
        # Pattern 1: Explicit "Tax Year YYYY" (highest priority)
        tax_year_match = re.search(r'tax year[:\s]+(\d{4})', text_lower)
        if tax_year_match:
            year = int(tax_year_match.group(1))
            if year <= max_allowed_year:
                evidence.append(f"Explicit 'Tax Year {year}' found in text")
                confidence_boost += 0.5  # Explicit year phrase
                return year, evidence, confidence_boost
            else:
                evidence.append(f"Future year {year} rejected (beyond {max_allowed_year})")
        
        # Pattern 2: "For the year ended [Month] [Day], YYYY"
        year_ended_match = re.search(r'for the year ended\s+\w+\s+\d{1,2},?\s+(\d{4})', text_lower)
        if year_ended_match:
            year = int(year_ended_match.group(1))
            if year <= max_allowed_year:
                evidence.append(f"Year {year} from 'year ended' phrase")
                confidence_boost += 0.5  # Explicit year phrase
                return year, evidence, confidence_boost
        
        # Pattern 3: "YYYY Form 1099" or "Form 1099-MISC YYYY"
        form_year_match = re.search(r'(?:(\d{4})\s+form\s+\d{4}|form\s+\d{4}(?:-\w+)?\s+(\d{4}))', text_lower)
        if form_year_match:
            year = int(form_year_match.group(1) or form_year_match.group(2))
            if year <= max_allowed_year:
                evidence.append(f"Year {year} from tax form header")
                confidence_boost += 0.4  # Form year is reliable
                return year, evidence, confidence_boost
        
        # Pattern 4: Collect all years from various date patterns
        year_frequencies = {}
        
        # MM/DD/YYYY or MM-DD-YYYY
        for match in re.finditer(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', text_lower):
            year = int(match.group(3))
            if 2000 <= year <= max_allowed_year:
                year_frequencies[year] = year_frequencies.get(year, 0) + 1
        
        # YYYY-MM-DD or YYYY/MM/DD
        for match in re.finditer(r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b', text_lower):
            year = int(match.group(1))
            if 2000 <= year <= max_allowed_year:
                year_frequencies[year] = year_frequencies.get(year, 0) + 1
        
        # Standalone 4-digit years (be conservative)
        for match in re.finditer(r'\b(20[0-2]\d)\b', text_lower):
            year = int(match.group(1))
            if 2000 <= year <= max_allowed_year:
                year_frequencies[year] = year_frequencies.get(year, 0) + 0.5  # Lower weight
        
        # Pattern 5: Year in filename
        filename_year_match = re.search(r'(20\d{2})', filename_lower)
        if filename_year_match:
            year = int(filename_year_match.group(1))
            if year <= max_allowed_year:
                year_frequencies[year] = year_frequencies.get(year, 0) + 2  # Higher weight
                evidence.append(f"Year {year} in filename")
                confidence_boost += 0.1  # Filename match
        
        # Find dominant year by frequency
        if year_frequencies:
            dominant_year = max(year_frequencies, key=year_frequencies.get)
            count = year_frequencies[dominant_year]
            evidence.append(f"Year {dominant_year} is dominant (appears {count:.0f} times)")
            return dominant_year, evidence, confidence_boost
        
        evidence.append("No valid year found in content")
        return None, evidence, 0.0
    
    def _infer_category(self, text_lower: str, filename_lower: str) -> tuple[Optional[str], list[str], float]:
        """Infer category from text content and filename.
        
        Category inference rules:
        - 1099 / W-2 → taxes
        - Insurance → insurance
        - Statement / Ending Balance → bank_statements
        
        Known document type adds +0.3 confidence boost.
        Filename match adds +0.1 confidence boost.
        
        Args:
            text_lower: Lowercase text content
            filename_lower: Lowercase filename
            
        Returns:
            Tuple of (category, evidence_list, confidence_boost)
        """
        evidence = []
        confidence_boost = 0.0
        matched_keywords = []
        
        # Check for known document types first (highest priority)
        known_types = {
            '1099': 'taxes',
            'w-2': 'taxes',
            'w2': 'taxes',
            'form 1099': 'taxes',
            'form w-2': 'taxes',
            'form w2': 'taxes',
            '1040': 'taxes',
            'tax return': 'taxes',
        }
        
        for keyword, category in known_types.items():
            if keyword in text_lower:
                evidence.append(f"Known document type '{keyword}' → {category}")
                confidence_boost += 0.3  # Known document type
                matched_keywords.append((keyword, category, 0.3))
        
        # Check filename for known types
        for keyword, category in known_types.items():
            if keyword in filename_lower:
                evidence.append(f"Known type '{keyword}' in filename → {category}")
                confidence_boost += 0.1  # Filename match (additional)
                if (keyword, category, 0.3) not in matched_keywords:
                    matched_keywords.append((keyword, category, 0.3))
        
        # If we found known types, use the first one
        if matched_keywords:
            _, category, _ = matched_keywords[0]
            return category, evidence, confidence_boost
        
        # Fall back to keyword scanning
        category_boosts = {}
        
        # Check filename for category keywords
        for keyword, (category, boost) in CATEGORY_KEYWORDS.items():
            if keyword in filename_lower:
                category_boosts[category] = category_boosts.get(category, 0.0) + boost + 0.1
                evidence.append(f"Keyword '{keyword}' in filename → {category}")
        
        # Scan text for category keywords
        for keyword, (category, boost) in CATEGORY_KEYWORDS.items():
            if keyword in text_lower:
                category_boosts[category] = category_boosts.get(category, 0.0) + boost
        
        if not category_boosts:
            evidence.append("No category keywords found")
            return None, evidence, 0.0
        
        # Get best category
        best_category = max(category_boosts, key=category_boosts.get)
        total_boost = category_boosts[best_category]
        
        evidence.append(f"Category '{best_category}' (confidence boost: +{total_boost:.2f})")
        
        return best_category, evidence, min(total_boost, 0.5)  # Cap category boost at 0.5

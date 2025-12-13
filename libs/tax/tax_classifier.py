"""Tax document classifier module.

Classifies tax documents by inferring year and category from content analysis.

Trust Boundaries:
    - PDF text extraction may fail silently (malformed PDFs, encryption)
    - Extracted text may be incomplete or garbled
    - Year/category inference is heuristic, not guaranteed accurate
    - Confidence scores are subjective estimates, not statistical probabilities
    - All operations are wrapped in error handling to prevent exceptions

Classification Strategy:
    1. Extract text from PDF using pdfplumber (no OCR)
    2. Scan for date patterns (multiple formats supported)
    3. Look for category keywords in content
    4. Calculate confidence based on evidence strength
    5. Return structured result with evidence trail

Confidence Levels:
    0.0 - 0.3: Low confidence (weak or ambiguous evidence)
    0.4 - 0.6: Medium confidence (single strong signal)
    0.7 - 0.9: High confidence (multiple signals agree)
    1.0:       Maximum confidence (definitive evidence)

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


# Category keywords mapping (keyword -> category, priority weight)
CATEGORY_KEYWORDS = {
    # Receipts
    'receipt': ('receipts', 2.0),
    'purchase': ('receipts', 1.5),
    'transaction': ('receipts', 1.0),
    'subtotal': ('receipts', 1.5),
    'total paid': ('receipts', 2.0),
    'payment received': ('receipts', 2.0),
    
    # Invoices
    'invoice': ('invoices', 3.0),
    'invoice number': ('invoices', 3.5),
    'invoice date': ('invoices', 3.0),
    'bill to': ('invoices', 2.5),
    'remit payment': ('invoices', 2.0),
    'due date': ('invoices', 1.5),
    'amount due': ('invoices', 2.0),
    
    # Bank statements
    'bank statement': ('bank_statements', 4.0),
    'statement period': ('bank_statements', 3.5),
    'account summary': ('bank_statements', 3.0),
    'beginning balance': ('bank_statements', 3.0),
    'ending balance': ('bank_statements', 3.0),
    'deposits': ('bank_statements', 2.0),
    'withdrawals': ('bank_statements', 2.0),
    'checking account': ('bank_statements', 2.5),
    'savings account': ('bank_statements', 2.5),
    
    # Statements (generic)
    'statement': ('statements', 1.5),
    'account statement': ('statements', 2.5),
    'monthly statement': ('statements', 2.0),
    'billing statement': ('statements', 2.0),
    
    # Forms
    'form 1099': ('forms', 4.0),
    'form w-2': ('forms', 4.0),
    'form 1040': ('forms', 4.0),
    'tax form': ('forms', 3.5),
    'irs': ('forms', 2.0),
    
    # Contracts
    'contract': ('contracts', 3.0),
    'agreement': ('contracts', 2.5),
    'terms and conditions': ('contracts', 2.0),
    'hereby agree': ('contracts', 2.5),
    'signatures': ('contracts', 1.5),
    
    # Correspondence
    'dear': ('correspondence', 1.5),
    'sincerely': ('correspondence', 1.5),
    'letter': ('correspondence', 2.0),
    're:': ('correspondence', 2.0),
    
    # Reports
    'report': ('reports', 2.0),
    'annual report': ('reports', 3.0),
    'quarterly report': ('reports', 3.0),
    'financial report': ('reports', 3.0),
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
        """Extract text from PDF file.
        
        Uses pdfplumber to extract text from all pages. Catches all exceptions
        to prevent errors from propagating.
        
        Trust Boundaries:
        - May fail on encrypted PDFs
        - May fail on malformed PDFs
        - May return incomplete text
        - May return garbled text from complex layouts
        
        Args:
            path: Path to PDF file
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            text_parts = []
            
            with pdfplumber.open(path) as pdf:
                # Extract from first 5 pages max (performance optimization)
                for page in pdf.pages[:5]:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            return "\n".join(text_parts) if text_parts else None
            
        except Exception as e:
            # Catch all exceptions (encrypted, malformed, etc.)
            return None
    
    def _classify_text(self, rel_path: str, text: str, filename: str) -> TaxClassificationResult:
        """Classify document based on text content and filename.
        
        Analyzes text for date patterns and category keywords. Combines
        multiple signals to determine confidence level.
        
        Args:
            rel_path: Relative path for result
            text: Extracted text content
            filename: Original filename
            
        Returns:
            TaxClassificationResult with inferred metadata
        """
        evidence = []
        
        # Normalize text for analysis
        text_lower = text.lower()
        text_sample = text[:3000]  # First ~3000 chars for efficiency
        
        # Infer year
        year, year_evidence = self._infer_year(text_sample, filename)
        evidence.extend(year_evidence)
        
        # Infer category
        category, category_evidence, category_score = self._infer_category(text_lower, filename)
        evidence.extend(category_evidence)
        
        # Calculate confidence
        confidence = self._calculate_confidence(year, year_evidence, category, category_score)
        
        return TaxClassificationResult(
            path=rel_path,
            inferred_year=year,
            inferred_category=category,
            confidence=confidence,
            evidence=evidence
        )
    
    def _infer_year(self, text: str, filename: str) -> tuple[Optional[int], list[str]]:
        """Infer year from text content and filename.
        
        Looks for various date patterns and extracts year. Prefers dates that
        appear to be statement dates, invoice dates, or transaction dates.
        
        Args:
            text: Text content to analyze
            filename: Original filename
            
        Returns:
            Tuple of (year, evidence_list)
        """
        evidence = []
        years_found = []
        
        # Pattern 1: Statement period dates (high confidence)
        period_pattern = r'(?:statement period|period|date range)[:\s]+.*?(\d{4})'
        for match in re.finditer(period_pattern, text, re.IGNORECASE):
            year = int(match.group(1))
            if 2000 <= year <= 2030:
                years_found.append((year, 3, "statement period"))
        
        # Pattern 2: Invoice/Statement dates
        date_labels = [
            'invoice date', 'statement date', 'date', 'transaction date',
            'billing date', 'issue date', 'due date'
        ]
        
        for label in date_labels:
            # MM/DD/YYYY or MM-DD-YYYY
            pattern = rf'{label}[:\s]+(\d{{1,2}})[/-](\d{{1,2}})[/-](\d{{4}})'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                year = int(match.group(3))
                if 2000 <= year <= 2030:
                    years_found.append((year, 2, f"{label}"))
            
            # YYYY-MM-DD
            pattern = rf'{label}[:\s]+(\d{{4}})[/-](\d{{1,2}})[/-](\d{{1,2}})'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                year = int(match.group(1))
                if 2000 <= year <= 2030:
                    years_found.append((year, 2, f"{label}"))
        
        # Pattern 3: Standalone dates anywhere in text
        # MM/DD/YYYY
        for match in re.finditer(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', text):
            year = int(match.group(3))
            if 2000 <= year <= 2030:
                years_found.append((year, 1, "date found"))
        
        # YYYY-MM-DD
        for match in re.finditer(r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b', text):
            year = int(match.group(1))
            if 2000 <= year <= 2030:
                years_found.append((year, 1, "date found"))
        
        # Pattern 4: Year in filename
        filename_year_match = re.search(r'(20\d{2})', filename)
        if filename_year_match:
            year = int(filename_year_match.group(1))
            if 2000 <= year <= 2030:
                years_found.append((year, 1.5, "filename"))
        
        # Pattern 5: Tax year mentions
        for match in re.finditer(r'tax year[:\s]+(\d{4})', text, re.IGNORECASE):
            year = int(match.group(1))
            if 2000 <= year <= 2030:
                years_found.append((year, 3, "tax year"))
        
        if not years_found:
            evidence.append("No year found in content")
            return None, evidence
        
        # Sort by priority and get most likely year
        years_found.sort(key=lambda x: x[1], reverse=True)
        
        # Use highest priority year
        best_year, priority, source = years_found[0]
        
        # Count occurrences of this year
        year_count = sum(1 for y, _, _ in years_found if y == best_year)
        
        evidence.append(f"Year {best_year} found from {source} ({year_count} occurrence(s))")
        
        return best_year, evidence
    
    def _infer_category(self, text_lower: str, filename: str) -> tuple[Optional[str], list[str], float]:
        """Infer category from text content and filename.
        
        Scans for category-specific keywords and calculates weighted score
        for each category. Returns highest scoring category.
        
        Args:
            text_lower: Lowercase text content
            filename: Original filename
            
        Returns:
            Tuple of (category, evidence_list, score)
        """
        evidence = []
        category_scores = {}
        
        # Check filename first
        filename_lower = filename.lower()
        for keyword, (category, weight) in CATEGORY_KEYWORDS.items():
            if keyword in filename_lower:
                category_scores[category] = category_scores.get(category, 0.0) + weight * 1.5
                evidence.append(f"Keyword '{keyword}' in filename → {category}")
        
        # Scan text for keywords
        for keyword, (category, weight) in CATEGORY_KEYWORDS.items():
            if keyword in text_lower:
                category_scores[category] = category_scores.get(category, 0.0) + weight
        
        if not category_scores:
            evidence.append("No category keywords found")
            return None, evidence, 0.0
        
        # Get best category
        best_category = max(category_scores, key=category_scores.get)
        best_score = category_scores[best_category]
        
        # Normalize score to 0-1 range (scores typically 2-15)
        normalized_score = min(best_score / 10.0, 1.0)
        
        evidence.append(f"Category '{best_category}' (score: {best_score:.1f})")
        
        # Show other strong contenders
        other_categories = [cat for cat in category_scores if cat != best_category and category_scores[cat] > 2.0]
        if other_categories:
            other_str = ", ".join(f"{cat}({category_scores[cat]:.1f})" for cat in other_categories[:2])
            evidence.append(f"Other possibilities: {other_str}")
        
        return best_category, evidence, normalized_score
    
    def _calculate_confidence(
        self,
        year: Optional[int],
        year_evidence: list[str],
        category: Optional[str],
        category_score: float
    ) -> float:
        """Calculate overall confidence score.
        
        Combines year and category confidence into overall score.
        
        Confidence Calculation:
        - No year or category: 0.0
        - Only year: 0.3-0.5 (depends on evidence)
        - Only category: 0.3-0.6 (depends on score)
        - Both: 0.5-0.9 (combined strength)
        
        Args:
            year: Inferred year (or None)
            year_evidence: Evidence supporting year
            category: Inferred category (or None)
            category_score: Normalized category score
            
        Returns:
            Confidence score 0.0-1.0
        """
        if year is None and category is None:
            return 0.0
        
        # Year confidence (based on evidence quality)
        year_conf = 0.0
        if year is not None:
            # Check for high-quality evidence
            has_statement_period = any('statement period' in e for e in year_evidence)
            has_labeled_date = any('date' in e and 'found' not in e for e in year_evidence)
            occurrence_count = sum(1 for e in year_evidence if 'occurrence' in e)
            
            if has_statement_period:
                year_conf = 0.8
            elif has_labeled_date:
                year_conf = 0.6
            else:
                year_conf = 0.4
            
            # Boost if multiple occurrences
            if occurrence_count > 3:
                year_conf = min(year_conf + 0.1, 0.9)
        
        # Category confidence (based on score)
        category_conf = category_score if category is not None else 0.0
        
        # Combined confidence
        if year is not None and category is not None:
            # Both found: weighted average, slightly boosted
            confidence = (year_conf * 0.5 + category_conf * 0.5) * 1.1
        elif year is not None:
            # Only year: use year confidence
            confidence = year_conf * 0.7
        else:
            # Only category: use category confidence
            confidence = category_conf * 0.8
        
        return min(confidence, 1.0)

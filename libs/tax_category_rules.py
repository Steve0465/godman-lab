"""
Tax Receipt Categorization Engine for TAX_MASTER_ARCHIVE

Provides intelligent classification of business receipts with category detection,
deductibility calculation, and confidence scoring.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List
import re


@dataclass
class ReceiptClassification:
    """
    Classification result for a tax receipt.
    
    Attributes:
        vendor: Normalized vendor name
        category: Primary tax category
        subcategory: Optional subcategory for detailed tracking
        deductible_amount: Dollar amount that is tax deductible
        deductibility_rate: Percentage deductible (0.0-1.0)
        needs_review: Whether manual review is required
        confidence: Classification confidence score (0.0-1.0)
        reason: Explanation of classification decision
    """
    vendor: str
    category: str
    subcategory: Optional[str]
    deductible_amount: float
    deductibility_rate: float
    needs_review: bool
    confidence: float
    reason: str


# Vendor-to-category mappings
VENDOR_MAP = {
    # Building Materials & Hardware
    "home depot": ("Materials", "Building Materials", 1.0),
    "lowe's": ("Materials", "Building Materials", 1.0),
    "lowes": ("Materials", "Building Materials", 1.0),
    "menards": ("Materials", "Building Materials", 1.0),
    "84 lumber": ("Materials", "Lumber", 1.0),
    "tractor supply": ("Materials", "Farm & Ranch", 1.0),
    
    # Pool-Specific
    "scp": ("Materials", "Pool Materials", 1.0),
    "scp distributors": ("Materials", "Pool Materials", 1.0),
    "leslie's pool": ("Materials", "Pool Materials", 1.0),
    "leslies pool": ("Materials", "Pool Materials", 1.0),
    "pinch a penny": ("Materials", "Pool Materials", 1.0),
    "poolcorp": ("Materials", "Pool Materials", 1.0),
    
    # Tools & Equipment
    "harbor freight": ("Tools", "Hand Tools", 1.0),
    "northern tool": ("Tools", "Power Tools", 1.0),
    "roll n vac": ("Tools", "Equipment", 1.0),
    "roll-n-vac": ("Tools", "Equipment", 1.0),
    "roll and vac": ("Tools", "Equipment", 1.0),
    "grainger": ("Tools", "Industrial Equipment", 1.0),
    
    # Equipment Rental
    "uhaul": ("Equipment Rental", "Vehicle Rental", 1.0),
    "u-haul": ("Equipment Rental", "Vehicle Rental", 1.0),
    "sunbelt rentals": ("Equipment Rental", "Equipment", 1.0),
    "united rentals": ("Equipment Rental", "Equipment", 1.0),
    
    # Automotive & Fuel
    "shell": ("Fuel", "Gasoline", 1.0),
    "exxon": ("Fuel", "Gasoline", 1.0),
    "chevron": ("Fuel", "Gasoline", 1.0),
    "bp": ("Fuel", "Gasoline", 1.0),
    "quiktrip": ("Fuel", "Gasoline", 1.0),
    "qt": ("Fuel", "Gasoline", 1.0),
    "racetrac": ("Fuel", "Gasoline", 1.0),
    "circle k": ("Fuel", "Gasoline", 1.0),
    "marathon": ("Fuel", "Gasoline", 1.0),
    "valero": ("Fuel", "Gasoline", 1.0),
    "autozone": ("Vehicle Maintenance", "Auto Parts", 1.0),
    "o'reilly": ("Vehicle Maintenance", "Auto Parts", 1.0),
    "oreilly": ("Vehicle Maintenance", "Auto Parts", 1.0),
    "advance auto": ("Vehicle Maintenance", "Auto Parts", 1.0),
    "napa": ("Vehicle Maintenance", "Auto Parts", 1.0),
    
    # Office Supplies
    "staples": ("Office Supplies", "Office Supplies", 1.0),
    "office depot": ("Office Supplies", "Office Supplies", 1.0),
    "officedepot": ("Office Supplies", "Office Supplies", 1.0),
    "office max": ("Office Supplies", "Office Supplies", 1.0),
    "officemax": ("Office Supplies", "Office Supplies", 1.0),
    "fedex office": ("Office Supplies", "Printing & Shipping", 1.0),
    "ups store": ("Office Supplies", "Printing & Shipping", 1.0),
    
    # Restaurants (50% deductible)
    "mcdonald's": ("Meals", "Fast Food", 0.5),
    "mcdonalds": ("Meals", "Fast Food", 0.5),
    "subway": ("Meals", "Fast Food", 0.5),
    "chick-fil-a": ("Meals", "Fast Food", 0.5),
    "chickfila": ("Meals", "Fast Food", 0.5),
    "panera": ("Meals", "Restaurant", 0.5),
    "chipotle": ("Meals", "Fast Food", 0.5),
    "starbucks": ("Meals", "Coffee", 0.5),
    "dunkin": ("Meals", "Coffee", 0.5),
    "waffle house": ("Meals", "Restaurant", 0.5),
    
    # Ambiguous Vendors (need context/review)
    "walmart": ("Ambiguous", None, 0.0),
    "target": ("Ambiguous", None, 0.0),
    "kroger": ("Ambiguous", None, 0.0),
    "publix": ("Ambiguous", None, 0.0),
    "safeway": ("Ambiguous", None, 0.0),
    "whole foods": ("Ambiguous", None, 0.0),
    "cvs": ("Ambiguous", None, 0.0),
    "walgreens": ("Ambiguous", None, 0.0),
    "amazon": ("Ambiguous", None, 0.0),
    "costco": ("Ambiguous", None, 0.0),
    "sam's club": ("Ambiguous", None, 0.0),
    "sams club": ("Ambiguous", None, 0.0),
}


# Keyword-based classification rules
# Format: (pattern, category, subcategory, deductibility_rate, confidence_boost)
KEYWORD_RULES: List[Tuple[str, str, Optional[str], float, float]] = [
    # Pool Materials
    (r"\bchlorine\b", "Materials", "Pool Materials", 1.0, 0.9),
    (r"\bshock\b", "Materials", "Pool Materials", 1.0, 0.9),
    (r"\btabs\b", "Materials", "Pool Materials", 1.0, 0.8),
    (r"\bstabilizer\b", "Materials", "Pool Materials", 1.0, 0.9),
    (r"\bmuriatic\s*acid\b", "Materials", "Pool Materials", 1.0, 0.95),
    (r"\bpool\s*sand\b", "Materials", "Pool Materials", 1.0, 0.9),
    (r"\bfilter\s*media\b", "Materials", "Pool Materials", 1.0, 0.85),
    (r"\balgaecide\b", "Materials", "Pool Materials", 1.0, 0.9),
    (r"\bclarifier\b", "Materials", "Pool Materials", 1.0, 0.85),
    (r"\bpool\s*cleaner\b", "Materials", "Pool Materials", 1.0, 0.85),
    
    # Plumbing Materials
    (r"\bpvc\b", "Materials", "Plumbing", 1.0, 0.85),
    (r"\bcoupler\b", "Materials", "Plumbing", 1.0, 0.8),
    (r"\belbow\b", "Materials", "Plumbing", 1.0, 0.8),
    (r"\bhose\b", "Materials", "Plumbing", 1.0, 0.75),
    (r"\bgasket\b", "Materials", "Plumbing", 1.0, 0.8),
    (r"\bfitting\b", "Materials", "Plumbing", 1.0, 0.8),
    (r"\bvalve\b", "Materials", "Plumbing", 1.0, 0.85),
    (r"\bpipe\b", "Materials", "Plumbing", 1.0, 0.8),
    (r"\bplumber\b", "Materials", "Plumbing", 1.0, 0.85),
    (r"\bdrain\b", "Materials", "Plumbing", 1.0, 0.75),
    
    # Electrical
    (r"\bwire\b", "Materials", "Electrical", 1.0, 0.8),
    (r"\bcable\b", "Materials", "Electrical", 1.0, 0.75),
    (r"\bswitch\b", "Materials", "Electrical", 1.0, 0.8),
    (r"\boutlet\b", "Materials", "Electrical", 1.0, 0.8),
    (r"\bcircuit\s*breaker\b", "Materials", "Electrical", 1.0, 0.9),
    (r"\belectrical\b", "Materials", "Electrical", 1.0, 0.85),
    
    # Tools
    (r"\bsaw\b", "Tools", "Power Tools", 1.0, 0.85),
    (r"\bdrill\b", "Tools", "Power Tools", 1.0, 0.85),
    (r"\bbit\b", "Tools", "Hand Tools", 1.0, 0.7),
    (r"\bwrench\b", "Tools", "Hand Tools", 1.0, 0.85),
    (r"\bhammer\b", "Tools", "Hand Tools", 1.0, 0.85),
    (r"\bscrewdriver\b", "Tools", "Hand Tools", 1.0, 0.85),
    (r"\bsander\b", "Tools", "Power Tools", 1.0, 0.85),
    (r"\blevel\b", "Tools", "Hand Tools", 1.0, 0.75),
    (r"\btape\s*measure\b", "Tools", "Hand Tools", 1.0, 0.8),
    (r"\bpliers\b", "Tools", "Hand Tools", 1.0, 0.85),
    
    # Fuel
    (r"\bgallon\b", "Fuel", "Gasoline", 1.0, 0.8),
    (r"\bgas\b", "Fuel", "Gasoline", 1.0, 0.7),
    (r"\bfuel\b", "Fuel", "Gasoline", 1.0, 0.85),
    (r"\bunleaded\b", "Fuel", "Gasoline", 1.0, 0.9),
    (r"\bdiesel\b", "Fuel", "Diesel", 1.0, 0.9),
    (r"\bpump\b", "Fuel", "Gasoline", 1.0, 0.75),
    (r"\bstation\b", "Fuel", "Gasoline", 1.0, 0.7),
    
    # Meals & Food (50% deductible)
    (r"\bmeal\b", "Meals", "Restaurant", 0.5, 0.8),
    (r"\bfood\b", "Meals", "Food", 0.5, 0.7),
    (r"\bdining\b", "Meals", "Restaurant", 0.5, 0.85),
    (r"\brestaurant\b", "Meals", "Restaurant", 0.5, 0.9),
    (r"\blunch\b", "Meals", "Restaurant", 0.5, 0.8),
    (r"\bdinner\b", "Meals", "Restaurant", 0.5, 0.8),
    (r"\bbreakfast\b", "Meals", "Restaurant", 0.5, 0.8),
    (r"\bcoffee\b", "Meals", "Coffee", 0.5, 0.75),
    
    # Office & Business
    (r"\bpaper\b", "Office Supplies", "Office Supplies", 1.0, 0.75),
    (r"\bprinter\b", "Office Supplies", "Equipment", 1.0, 0.8),
    (r"\bink\b", "Office Supplies", "Supplies", 1.0, 0.8),
    (r"\btoner\b", "Office Supplies", "Supplies", 1.0, 0.85),
    (r"\benvelope\b", "Office Supplies", "Supplies", 1.0, 0.85),
    (r"\bpen\b", "Office Supplies", "Supplies", 1.0, 0.7),
    (r"\bpencil\b", "Office Supplies", "Supplies", 1.0, 0.7),
    (r"\bnotebook\b", "Office Supplies", "Supplies", 1.0, 0.75),
    (r"\bstapler\b", "Office Supplies", "Supplies", 1.0, 0.8),
    
    # Cleaning & Maintenance
    (r"\bbroom\b", "Materials", "Cleaning", 1.0, 0.8),
    (r"\bmop\b", "Materials", "Cleaning", 1.0, 0.8),
    (r"\bvacuum\b", "Tools", "Equipment", 1.0, 0.8),
    (r"\bcleaner\b", "Materials", "Cleaning", 1.0, 0.75),
    (r"\bbleach\b", "Materials", "Cleaning", 1.0, 0.75),
    (r"\bsoap\b", "Materials", "Cleaning", 1.0, 0.7),
]


def normalize_text(text: str) -> str:
    """
    Normalize text for pattern matching.
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Lowercase text with extra whitespace removed
    """
    return " ".join(text.lower().strip().split())


def lookup_vendor(vendor: str) -> Optional[Tuple[str, Optional[str], float]]:
    """
    Look up vendor in the vendor map.
    
    Args:
        vendor: Normalized vendor name
        
    Returns:
        Tuple of (category, subcategory, deductibility_rate) or None
    """
    return VENDOR_MAP.get(vendor)


def apply_keyword_rules(text: str) -> List[Tuple[str, Optional[str], float, float]]:
    """
    Apply keyword-based classification rules to text.
    
    Args:
        text: Normalized text to analyze
        
    Returns:
        List of (category, subcategory, deductibility_rate, confidence) matches
    """
    matches = []
    for pattern, category, subcategory, rate, confidence in KEYWORD_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append((category, subcategory, rate, confidence))
    return matches


def resolve_classification(
    vendor_result: Optional[Tuple[str, Optional[str], float]],
    keyword_matches: List[Tuple[str, Optional[str], float, float]],
    vendor: str
) -> Tuple[str, Optional[str], float, float, bool, str]:
    """
    Resolve final classification from vendor and keyword signals.
    
    Args:
        vendor_result: Result from vendor lookup
        keyword_matches: Matches from keyword rules
        vendor: Normalized vendor name
        
    Returns:
        Tuple of (category, subcategory, deductibility_rate, confidence, needs_review, reason)
    """
    # Case 1: Known vendor with clear category
    if vendor_result:
        category, subcategory, rate = vendor_result
        
        # Check if vendor is ambiguous
        if category == "Ambiguous":
            # Try to resolve with keywords
            if keyword_matches:
                # Use highest confidence keyword match
                best_match = max(keyword_matches, key=lambda x: x[3])
                kw_category, kw_subcategory, kw_rate, kw_confidence = best_match
                
                return (
                    kw_category,
                    kw_subcategory,
                    kw_rate,
                    kw_confidence * 0.9,  # Slight penalty for ambiguous vendor
                    False,
                    f"Ambiguous vendor '{vendor}' resolved by keyword detection"
                )
            else:
                return (
                    "Unknown",
                    None,
                    0.0,
                    0.5,
                    True,
                    f"Ambiguous vendor '{vendor}' with no clear keywords - needs review"
                )
        
        # Known vendor - check for keyword conflicts
        if keyword_matches:
            # Check if keywords agree with vendor category
            keyword_categories = set(m[0] for m in keyword_matches)
            if category not in keyword_categories and len(keyword_categories) > 0:
                # Potential conflict - flag for review
                return (
                    category,
                    subcategory,
                    rate,
                    0.7,
                    True,
                    f"Vendor suggests '{category}' but keywords suggest {keyword_categories} - needs review"
                )
        
        # Clean match - high confidence
        return (
            category,
            subcategory,
            rate,
            0.95,
            False,
            f"Known vendor '{vendor}' with clear category"
        )
    
    # Case 2: Unknown vendor with keyword matches
    if keyword_matches:
        # Check for conflicting signals
        categories = [m[0] for m in keyword_matches]
        rates = [m[2] for m in keyword_matches]
        
        if len(set(categories)) > 1 or len(set(rates)) > 1:
            # Conflicting signals - flag for review
            best_match = max(keyword_matches, key=lambda x: x[3])
            kw_category, kw_subcategory, kw_rate, kw_confidence = best_match
            
            return (
                kw_category,
                kw_subcategory,
                kw_rate,
                kw_confidence * 0.6,
                True,
                f"Unknown vendor with conflicting keyword signals - needs review"
            )
        
        # Consistent keywords - good confidence
        best_match = max(keyword_matches, key=lambda x: x[3])
        kw_category, kw_subcategory, kw_rate, kw_confidence = best_match
        
        return (
            kw_category,
            kw_subcategory,
            kw_rate,
            kw_confidence * 0.85,
            False,
            f"Unknown vendor classified by keywords: {kw_category}"
        )
    
    # Case 3: Unknown vendor, no keywords
    return (
        "Unknown",
        None,
        0.0,
        0.3,
        True,
        f"Unknown vendor '{vendor}' with no recognizable keywords - needs review"
    )


def classify_receipt(vendor: str, text: str, amount: float) -> ReceiptClassification:
    """
    Classify a receipt for tax purposes.
    
    Applies vendor recognition, keyword detection, and business logic to determine
    the appropriate tax category, deductibility rate, and confidence score.
    
    Args:
        vendor: Vendor/merchant name
        text: Receipt text content (description, items, etc.)
        amount: Receipt total amount in dollars
        
    Returns:
        ReceiptClassification with complete categorization details
        
    Example:
        >>> classify_receipt("Home Depot", "2x4 lumber, saw blade", 45.99)
        ReceiptClassification(
            vendor='home depot',
            category='Materials',
            subcategory='Building Materials',
            deductible_amount=45.99,
            deductibility_rate=1.0,
            needs_review=False,
            confidence=0.95,
            reason='Known vendor...'
        )
    """
    # Normalize inputs
    vendor_normalized = normalize_text(vendor)
    text_normalized = normalize_text(text)
    combined_text = f"{vendor_normalized} {text_normalized}"
    
    # Lookup vendor
    vendor_result = lookup_vendor(vendor_normalized)
    
    # Apply keyword rules
    keyword_matches = apply_keyword_rules(combined_text)
    
    # Resolve classification
    category, subcategory, rate, confidence, needs_review, reason = resolve_classification(
        vendor_result,
        keyword_matches,
        vendor_normalized
    )
    
    # Calculate deductible amount
    deductible_amount = round(amount * rate, 2)
    
    # Additional validation checks
    if amount <= 0:
        needs_review = True
        confidence *= 0.5
        reason += " | Invalid amount"
    
    if amount > 10000:
        needs_review = True
        reason += " | Large amount - verify classification"
    
    return ReceiptClassification(
        vendor=vendor_normalized,
        category=category,
        subcategory=subcategory,
        deductible_amount=deductible_amount,
        deductibility_rate=rate,
        needs_review=needs_review,
        confidence=round(confidence, 2),
        reason=reason
    )


def batch_classify_receipts(
    receipts: List[Tuple[str, str, float]]
) -> List[ReceiptClassification]:
    """
    Classify multiple receipts in batch.
    
    Args:
        receipts: List of (vendor, text, amount) tuples
        
    Returns:
        List of ReceiptClassification results
    """
    return [classify_receipt(vendor, text, amount) for vendor, text, amount in receipts]


def get_category_summary(classifications: List[ReceiptClassification]) -> dict:
    """
    Generate summary statistics for a list of classifications.
    
    Args:
        classifications: List of ReceiptClassification results
        
    Returns:
        Dictionary with category totals and review counts
    """
    summary = {
        "total_receipts": len(classifications),
        "total_amount": 0.0,
        "total_deductible": 0.0,
        "needs_review_count": 0,
        "categories": {},
        "avg_confidence": 0.0
    }
    
    for classification in classifications:
        # Update totals
        summary["total_amount"] += classification.deductible_amount / classification.deductibility_rate if classification.deductibility_rate > 0 else 0
        summary["total_deductible"] += classification.deductible_amount
        summary["avg_confidence"] += classification.confidence
        
        if classification.needs_review:
            summary["needs_review_count"] += 1
        
        # Update category totals
        category = classification.category
        if category not in summary["categories"]:
            summary["categories"][category] = {
                "count": 0,
                "deductible_amount": 0.0
            }
        
        summary["categories"][category]["count"] += 1
        summary["categories"][category]["deductible_amount"] += classification.deductible_amount
    
    # Calculate average confidence
    if len(classifications) > 0:
        summary["avg_confidence"] = round(summary["avg_confidence"] / len(classifications), 2)
    
    # Round totals
    summary["total_amount"] = round(summary["total_amount"], 2)
    summary["total_deductible"] = round(summary["total_deductible"], 2)
    
    return summary


# Utility function for testing and validation
def validate_classification_rules() -> dict:
    """
    Validate that classification rules are consistent and complete.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "vendor_count": len(VENDOR_MAP),
        "keyword_rule_count": len(KEYWORD_RULES),
        "ambiguous_vendors": [],
        "duplicate_vendors": [],
        "rate_distribution": {
            "100%": 0,
            "50%": 0,
            "0%": 0
        }
    }
    
    # Check for ambiguous vendors
    for vendor, (category, _, rate) in VENDOR_MAP.items():
        if category == "Ambiguous":
            results["ambiguous_vendors"].append(vendor)
        
        # Count rate distribution
        if rate == 1.0:
            results["rate_distribution"]["100%"] += 1
        elif rate == 0.5:
            results["rate_distribution"]["50%"] += 1
        elif rate == 0.0:
            results["rate_distribution"]["0%"] += 1
    
    # Check for potential duplicates (similar names)
    vendors = list(VENDOR_MAP.keys())
    for i, v1 in enumerate(vendors):
        for v2 in vendors[i+1:]:
            if v1.replace(" ", "") == v2.replace(" ", "") or v1.replace("-", "") == v2.replace("-", ""):
                results["duplicate_vendors"].append((v1, v2))
    
    return results

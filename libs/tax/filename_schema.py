import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional

class OwnerTag(str, Enum):
    STEVE = "STEVE"
    ASHLEIGH = "ASHLEIGH"
    JOINT = "JOINT"

class IntentTag(str, Enum):
    BIZ = "BIZ"
    PERSONAL = "PERSONAL"
    MIXED = "MIXED"

class StatusTag(str, Enum):
    OK = "OK"
    REVIEW = "REVIEW"

@dataclass
class TaxFilenameParts:
    date: date
    owner: OwnerTag
    intent: IntentTag
    category: str
    source: str
    description: str
    ext: str
    amount: Optional[Decimal] = None
    status: Optional[StatusTag] = None

def sanitize_token(s: str) -> str:
    """
    Sanitize a string to be a valid filename token:
    - Uppercase
    - Replace non-alphanumeric chars with underscore
    - Collapse multiple underscores
    - Strip leading/trailing underscores
    """
    if not s:
        return "UNKNOWN"
    s = s.upper()
    s = re.sub(r'[^A-Z0-9]', '_', s)
    s = re.sub(r'_+', '_', s)
    s = s.strip('_')
    return s or "UNKNOWN"

def build_tax_filename(parts: TaxFilenameParts) -> str:
    """
    Build a filename from parts:
    YYYY-MM-DD__OWNER__INTENT__CATEGORY__SOURCE__AMOUNT__DESCRIPTION(__STATUS).ext
    """
    date_str = parts.date.strftime("%Y-%m-%d")
    
    # Optional amount
    amount_str = ""
    if parts.amount is not None:
        # 2 decimals, dot, no commas
        amount_str = f"__{parts.amount:.2f}"
    
    # Optional status
    status_str = ""
    if parts.status:
        status_str = f"__{parts.status.value}"
        
    filename = (
        f"{date_str}__{parts.owner.value}__{parts.intent.value}__"
        f"{sanitize_token(parts.category)}__{sanitize_token(parts.source)}"
        f"{amount_str}__{sanitize_token(parts.description)}{status_str}.{parts.ext}"
    )
    return filename

def parse_tax_filename(filename: str) -> Optional[TaxFilenameParts]:
    """
    Parse a filename into TaxFilenameParts.
    Returns None if it doesn't match the schema.
    """
    path = Path(filename)
    name = path.stem
    ext = path.suffix.lstrip('.')
    
    # Split by double underscore
    parts = name.split('__')
    
    # Minimum parts: DATE, OWNER, INTENT, CATEGORY, SOURCE, DESCRIPTION (6 parts)
    if len(parts) < 6:
        return None
        
    # 1. Date
    try:
        file_date = datetime.strptime(parts[0], "%Y-%m-%d").date()
    except ValueError:
        return None
        
    # 2. Owner
    try:
        owner = OwnerTag(parts[1])
    except ValueError:
        return None
        
    # 3. Intent
    try:
        intent = IntentTag(parts[2])
    except ValueError:
        return None
        
    # 4. Category
    category = parts[3]
    
    # 5. Source
    source = parts[4]
    
    # Remaining parts handle Amount, Description, Status
    # We need to identify if amount and status are present.
    # Amount looks like a decimal number.
    # Status is one of the StatusTag values.
    
    remaining = parts[5:]
    amount: Optional[Decimal] = None
    status: Optional[StatusTag] = None
    description_parts = []
    
    # Check for Status at the end
    if remaining and remaining[-1] in [t.value for t in StatusTag]:
        status = StatusTag(remaining[-1])
        remaining.pop()
        
    # Check for Amount at the beginning of remaining
    if remaining:
        try:
            # Check if first remaining part is a valid amount
            # It should be a number, potentially with a dot
            possible_amount = remaining[0]
            # Simple check: must contain digits, maybe one dot
            if re.match(r'^\d+(\.\d+)?$', possible_amount):
                amount = Decimal(possible_amount)
                remaining.pop(0)
        except Exception:
            pass
            
    # Whatever is left is the description
    if not remaining:
        # Description is mandatory in schema, but if missing in filename, 
        # we might fail or just assign empty? 
        # The prompt says "DESCRIPTION" is a part.
        # If we consumed everything for amount/status, then description is missing.
        # Let's assume description is mandatory.
        return None
        
    description = "_".join(remaining)
    
    return TaxFilenameParts(
        date=file_date,
        owner=owner,
        intent=intent,
        category=category,
        source=source,
        description=description,
        ext=ext,
        amount=amount,
        status=status
    )

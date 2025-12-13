from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from libs.tax.filename_schema import OwnerTag, TaxFilenameParts

@dataclass
class AllocationRule:
    source_token: str
    keywords: List[str]
    splits: Dict[OwnerTag, int]  # Percentage 0-100

    def matches(self, parts: TaxFilenameParts) -> bool:
        if parts.source != self.source_token:
            return False
        if not self.keywords:
            return True
        # Check if any keyword is in description
        desc = parts.description
        return any(k in desc for k in self.keywords)

DEFAULT_RULES = [
    AllocationRule(
        source_token="ATT",
        keywords=[],
        splits={OwnerTag.STEVE: 60, OwnerTag.ASHLEIGH: 40}
    ),
    AllocationRule(
        source_token="MLGW",
        keywords=[],
        splits={OwnerTag.STEVE: 50, OwnerTag.ASHLEIGH: 50}
    ),
    AllocationRule(
        source_token="COMCAST",
        keywords=[],
        splits={OwnerTag.STEVE: 50, OwnerTag.ASHLEIGH: 50}
    ),
    AllocationRule(
        source_token="VERIZON",
        keywords=[],
        splits={OwnerTag.STEVE: 50, OwnerTag.ASHLEIGH: 50}
    ),
]

def suggest_allocation(parts: TaxFilenameParts, rules: List[AllocationRule] = None) -> Optional[Dict[OwnerTag, int]]:
    if rules is None:
        rules = DEFAULT_RULES
        
    for rule in rules:
        if rule.matches(parts):
            return rule.splits
            
    return None

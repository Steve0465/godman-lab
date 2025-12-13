"""
Archive scoring logic for the Unified Archive Framework.

Provides integrity scoring based on real corruption issues only.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ScoringConfig:
    """Configuration for archive integrity scoring."""
    max_score: int = 100
    zero_byte_penalty: int = 5
    hash_mismatch_penalty: int = 3
    missing_file_penalty: int = 2


def calculate_integrity_score(
    zero_byte_files: List[str],
    hash_mismatches: List[str],
    missing_files: List[str],
    config: ScoringConfig = None
) -> Dict[str, Any]:
    """
    Calculate archive integrity score based on corruption issues.
    
    Only deducts points for real data corruption:
    - Zero-byte files: -5 points each
    - Hash mismatches: -3 points each
    - Missing files: -2 points each
    
    Documentation issues and ordering problems generate warnings only.
    
    Args:
        zero_byte_files: List of zero-byte file paths
        hash_mismatches: List of files with hash mismatches
        missing_files: List of missing file paths
        config: Optional scoring configuration
        
    Returns:
        Dictionary containing:
            - integrity_score: Final score (0-100)
            - max_score: Maximum possible score
            - deductions: Breakdown of point deductions
            - critical_issues: Count of critical problems
    """
    if config is None:
        config = ScoringConfig()
    
    score = config.max_score
    deductions = {}
    
    # Deduct for zero-byte files
    zero_byte_count = len(zero_byte_files)
    zero_byte_deduction = zero_byte_count * config.zero_byte_penalty
    if zero_byte_deduction > 0:
        score -= zero_byte_deduction
        deductions["zero_byte_files"] = {
            "count": zero_byte_count,
            "penalty_per_file": config.zero_byte_penalty,
            "total_deduction": zero_byte_deduction
        }
    
    # Deduct for hash mismatches
    hash_mismatch_count = len(hash_mismatches)
    hash_mismatch_deduction = hash_mismatch_count * config.hash_mismatch_penalty
    if hash_mismatch_deduction > 0:
        score -= hash_mismatch_deduction
        deductions["hash_mismatches"] = {
            "count": hash_mismatch_count,
            "penalty_per_file": config.hash_mismatch_penalty,
            "total_deduction": hash_mismatch_deduction
        }
    
    # Deduct for missing files
    missing_file_count = len(missing_files)
    missing_file_deduction = missing_file_count * config.missing_file_penalty
    if missing_file_deduction > 0:
        score -= missing_file_deduction
        deductions["missing_files"] = {
            "count": missing_file_count,
            "penalty_per_file": config.missing_file_penalty,
            "total_deduction": missing_file_deduction
        }
    
    # Ensure score doesn't go below 0
    score = max(0, score)
    
    critical_issues = zero_byte_count + hash_mismatch_count + missing_file_count
    
    return {
        "integrity_score": score,
        "max_score": config.max_score,
        "deductions": deductions,
        "critical_issues": critical_issues,
        "is_healthy": score >= 95 and critical_issues == 0
    }


def calculate_completeness_score(
    expected_files: int,
    actual_files: int,
    missing_files: int
) -> Dict[str, Any]:
    """
    Calculate archive completeness as a percentage.
    
    Args:
        expected_files: Number of files expected
        actual_files: Number of files found
        missing_files: Number of missing files
        
    Returns:
        Dictionary with completeness metrics
    """
    if expected_files == 0:
        completeness = 100.0
    else:
        completeness = ((expected_files - missing_files) / expected_files) * 100
        completeness = max(0.0, min(100.0, completeness))
    
    return {
        "completeness_percentage": round(completeness, 2),
        "expected_files": expected_files,
        "actual_files": actual_files,
        "missing_files": missing_files,
        "extra_files": max(0, actual_files - expected_files)
    }

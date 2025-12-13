"""
General-purpose archive validator for the Unified Archive Framework.

Validates archive integrity, detects corruption, and generates detailed reports.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .base_archive import BaseArchive
from .archive_scoring import calculate_integrity_score, calculate_completeness_score


@dataclass
class ArchiveValidationResult:
    """
    Result of archive validation containing stats, scores, and issues.
    """
    archive_name: str
    validation_time: str
    stats: Dict[str, Any]
    integrity_score: int
    completeness_score: float
    critical_problems: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    zero_byte_files: List[str] = field(default_factory=list)
    hash_mismatches: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)
    extra_files: List[str] = field(default_factory=list)
    manifest_exists: bool = True
    hash_index_exists: bool = True
    is_healthy: bool = True
    
    def __str__(self) -> str:
        """Generate a human-readable report."""
        lines = [
            f"Archive Validation Report: {self.archive_name}",
            f"Validation Time: {self.validation_time}",
            f"",
            f"Integrity Score: {self.integrity_score}/100",
            f"Completeness: {self.completeness_score}%",
            f"Health Status: {'✓ HEALTHY' if self.is_healthy else '✗ ISSUES DETECTED'}",
            f"",
            f"Statistics:",
        ]
        
        for key, value in self.stats.items():
            lines.append(f"  {key}: {value}")
        
        if self.critical_problems:
            lines.append(f"\nCritical Problems ({len(self.critical_problems)}):")
            for problem in self.critical_problems[:10]:
                lines.append(f"  ✗ {problem}")
            if len(self.critical_problems) > 10:
                lines.append(f"  ... and {len(self.critical_problems) - 10} more")
        
        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings[:10]:
                lines.append(f"  ⚠ {warning}")
            if len(self.warnings) > 10:
                lines.append(f"  ... and {len(self.warnings) - 10} more")
        
        return "\n".join(lines)


class ArchiveValidator:
    """
    General-purpose validator for any archive type.
    
    Performs comprehensive validation including:
    - Filesystem scanning
    - Zero-byte file detection
    - Manifest comparison
    - Hash index verification
    - Integrity scoring
    """
    
    def __init__(self, archive: BaseArchive):
        """
        Initialize the validator.
        
        Args:
            archive: BaseArchive instance to validate
        """
        self.archive = archive
    
    def validate(self, check_hashes: bool = True) -> ArchiveValidationResult:
        """
        Perform comprehensive archive validation.
        
        Args:
            check_hashes: Whether to verify file hashes (can be slow for large archives)
            
        Returns:
            ArchiveValidationResult with complete validation results
        """
        validation_time = datetime.now().isoformat()
        
        # Scan filesystem
        all_files = self.archive.list_files(relative=True)
        data_files = [f for f in all_files if not self.archive.is_metadata(f)]
        
        # Detect zero-byte files
        zero_byte_files = self._detect_zero_byte_files(all_files)
        
        # Check manifest
        manifest_exists = self.archive.get_manifest_path().exists()
        manifest_files, manifest_missing, manifest_extra = self._check_manifest(data_files)
        
        # Check hash index
        hash_index_exists = self.archive.get_hash_index_path().exists()
        hash_mismatches = []
        if check_hashes and hash_index_exists:
            hash_mismatches = self._check_hash_index()
        
        # Calculate scores
        scoring_result = calculate_integrity_score(
            zero_byte_files=[str(f) for f in zero_byte_files],
            hash_mismatches=[str(f) for f in hash_mismatches],
            missing_files=[str(f) for f in manifest_missing]
        )
        
        completeness_result = calculate_completeness_score(
            expected_files=len(manifest_files) if manifest_exists else len(data_files),
            actual_files=len(data_files),
            missing_files=len(manifest_missing)
        )
        
        # Compile critical problems
        critical_problems = []
        for f in zero_byte_files:
            critical_problems.append(f"Zero-byte file: {f}")
        for f in hash_mismatches:
            critical_problems.append(f"Hash mismatch: {f}")
        for f in manifest_missing:
            critical_problems.append(f"Missing file (in manifest): {f}")
        
        # Compile warnings
        warnings = []
        if not manifest_exists:
            warnings.append("MANIFEST.md not found")
        if not hash_index_exists:
            warnings.append("HASH_INDEX.md not found")
        for f in manifest_extra:
            warnings.append(f"Extra file (not in manifest): {f}")
        
        # Build stats
        file_classification = self.archive.classify_files()
        stats = {
            "total_files": len(all_files),
            "data_files": len(data_files),
            "metadata_files": len(file_classification["metadata"]),
            "pdf_files": len(file_classification["pdf"]),
            "csv_files": len(file_classification["csv"]),
            "image_files": len(file_classification["image"]),
            "years": len(self.archive.list_years()),
            "zero_byte_files": len(zero_byte_files),
            "hash_mismatches": len(hash_mismatches),
            "missing_files": len(manifest_missing),
            "extra_files": len(manifest_extra)
        }
        
        # Determine health
        is_healthy = (
            scoring_result["is_healthy"] and
            len(critical_problems) == 0 and
            manifest_exists and
            hash_index_exists
        )
        
        return ArchiveValidationResult(
            archive_name=self.archive.name,
            validation_time=validation_time,
            stats=stats,
            integrity_score=scoring_result["integrity_score"],
            completeness_score=completeness_result["completeness_percentage"],
            critical_problems=critical_problems,
            warnings=warnings,
            zero_byte_files=[str(f) for f in zero_byte_files],
            hash_mismatches=[str(f) for f in hash_mismatches],
            missing_files=[str(f) for f in manifest_missing],
            extra_files=[str(f) for f in manifest_extra],
            manifest_exists=manifest_exists,
            hash_index_exists=hash_index_exists,
            is_healthy=is_healthy
        )
    
    def _detect_zero_byte_files(self, files: List[Path]) -> List[Path]:
        """
        Detect files with zero bytes.
        
        Args:
            files: List of file paths to check
            
        Returns:
            List of zero-byte file paths
        """
        zero_byte = []
        for file in files:
            try:
                if self.archive.get_file_size(file) == 0:
                    zero_byte.append(file)
            except (OSError, IOError):
                pass
        return zero_byte
    
    def _check_manifest(self, actual_files: List[Path]) -> tuple:
        """
        Compare actual files against manifest.
        
        Args:
            actual_files: List of actual file paths in archive
            
        Returns:
            Tuple of (manifest_files, missing_files, extra_files)
        """
        manifest_path = self.archive.get_manifest_path()
        if not manifest_path.exists():
            return [], [], actual_files
        
        manifest_files = self._parse_manifest(manifest_path)
        manifest_set = set(manifest_files)
        actual_set = set(actual_files)
        
        missing = sorted(manifest_set - actual_set)
        extra = sorted(actual_set - manifest_set)
        
        return manifest_files, missing, extra
    
    def _parse_manifest(self, manifest_path: Path) -> List[Path]:
        """
        Parse manifest file to extract file list.
        
        Args:
            manifest_path: Path to MANIFEST.md
            
        Returns:
            List of Path objects from manifest
        """
        files = []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Look for lines that start with "- " or "* " (markdown list items)
                    if line.startswith("- ") or line.startswith("* "):
                        # Extract filename, handling various formats
                        parts = line[2:].strip().split()
                        if parts:
                            # First part should be the filename
                            filename = parts[0].strip("`")
                            if filename and not filename.startswith("#"):
                                files.append(Path(filename))
        except (OSError, IOError):
            pass
        
        return files
    
    def _check_hash_index(self) -> List[Path]:
        """
        Check hash index and detect mismatches.
        
        Returns:
            List of files with hash mismatches
        """
        hash_index_path = self.archive.get_hash_index_path()
        if not hash_index_path.exists():
            return []
        
        mismatches = []
        hash_map = self._parse_hash_index(hash_index_path)
        
        for file_path, expected_hash in hash_map.items():
            full_path = self.archive.root / file_path
            if full_path.exists():
                try:
                    actual_hash = self.archive.compute_file_hash(file_path)
                    if actual_hash != expected_hash:
                        mismatches.append(file_path)
                except (OSError, IOError):
                    pass
        
        return mismatches
    
    def _parse_hash_index(self, hash_index_path: Path) -> Dict[Path, str]:
        """
        Parse hash index file.
        
        Args:
            hash_index_path: Path to HASH_INDEX.md
            
        Returns:
            Dictionary mapping file paths to hash values
        """
        hash_map = {}
        try:
            with open(hash_index_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Look for lines with format: hash filename or | hash | filename |
                    if "|" in line:
                        parts = [p.strip() for p in line.split("|") if p.strip()]
                        if len(parts) >= 2 and not parts[0].startswith("-"):
                            hash_val = parts[0].strip("`")
                            filename = parts[1].strip("`")
                            if hash_val and filename and len(hash_val) == 64:
                                hash_map[Path(filename)] = hash_val
                    elif line and not line.startswith("#") and not line.startswith("-"):
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            hash_val, filename = parts
                            if len(hash_val) == 64:
                                hash_map[Path(filename)] = hash_val
        except (OSError, IOError):
            pass
        
        return hash_map

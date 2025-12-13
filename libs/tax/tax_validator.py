"""Tax archive validator module.

Validates tax archive structure, detects duplicates, and identifies issues.

Directory Exclusions:
    Top-level directories in EXCLUDED_TOP_LEVEL_DIRS are completely skipped
    during scanning. Files under these directories will not appear as orphans,
    warnings, or in any validation results. This is useful for:
    - Metadata folders (_metadata, .metadata)
    - Version control (.git, .svn)
    - Build artifacts (__pycache__, .pytest_cache)
    - System folders (.DS_Store parent directories)
    
    Excluded directories are checked at the top level of the archive only.
    Nested directories with similar names are not automatically excluded.

See TAX_VALIDATOR_IMPLEMENTATION.md for specifications.
"""

from pathlib import Path
from typing import Dict, List, Set
import hashlib
import re

from .tax_models import TaxFileRecord, ValidationIssue, ValidationReport


# Allowed tax categories (folder names)
ALLOWED_CATEGORIES = {
    "receipts",
    "statements",
    "bank_statements",
    "invoices",
    "contracts",
    "forms",
    "documents",
    "correspondence",
    "reports",
    "personal"
}

# Top-level directories to exclude from validation
# Files under these directories are completely ignored and won't appear as orphans
EXCLUDED_TOP_LEVEL_DIRS = {
    "_metadata",
    "metadata",
    ".git",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "node_modules",
    ".venv",
    "venv"
}


class TaxValidator:
    """Validates tax archive structure and identifies issues.
    
    Performs comprehensive validation including:
    - Year and category folder validation
    - Duplicate detection (by MD5 and filename)
    - Orphaned file detection
    - iCloud placeholder detection
    - Misplaced file detection
    
    Directory Exclusions:
    - Top-level directories in EXCLUDED_TOP_LEVEL_DIRS are skipped entirely
    - Files under excluded directories don't appear in validation results
    - No orphan warnings generated for excluded files
    - Useful for metadata, version control, and build artifacts
    
    Uses single directory walk for efficiency and streaming MD5 computation
    for large file safety.
    """
    
    def __init__(self, root_path: Path):
        """Initialize tax validator.
        
        Args:
            root_path: Root directory of tax archive to validate
        """
        self.root_path = Path(root_path)
        self._hash_cache: Dict[str, str] = {}
    
    def scan(self) -> List[TaxFileRecord]:
        """Scan tax archive and create file records.
        
        Walks the archive once, creating a TaxFileRecord for each file with:
        - Inferred year from folder name (YYYY or "Personal")
        - Inferred category from folder structure
        - File size from stat
        - MD5 hash computed in streaming fashion
        
        Files under excluded directories (EXCLUDED_TOP_LEVEL_DIRS) are skipped
        entirely and will not appear in the results.
        
        Returns:
            List of TaxFileRecord objects for all non-excluded files in archive
        """
        records = []
        
        # Single directory walk using rglob
        for file_path in self.root_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Skip excluded directories
            if self._is_excluded(file_path):
                continue
            
            # Get relative path for cleaner records
            try:
                rel_path = file_path.relative_to(self.root_path)
            except ValueError:
                rel_path = file_path
            
            # Infer year from path
            year = self._infer_year(file_path)
            
            # Infer category from path
            category = self._infer_category(file_path)
            
            # Get file size
            try:
                size_bytes = file_path.stat().st_size
            except (OSError, IOError):
                size_bytes = 0
            
            # Compute MD5 hash (streaming, chunked) - skip for 0-byte files
            if size_bytes > 0:
                md5_hash = self._compute_md5(file_path)
            else:
                md5_hash = None
            
            # Create record
            record = TaxFileRecord(
                path=str(rel_path),
                year=year,
                category=category,
                size_bytes=size_bytes,
                md5=md5_hash
            )
            
            records.append(record)
        
        return records
    
    def validate(self) -> ValidationReport:
        """Validate tax archive and generate comprehensive report.
        
        Performs validation checks:
        - Structural: year folders, category folders, orphan files
        - Duplicates: by MD5 hash and filename
        - iCloud placeholders: zero-byte files
        - Misplaced files: wrong year or category
        
        Returns:
            ValidationReport with all issues found and validity status
        """
        # Scan all files
        records = self.scan()
        
        # Initialize report
        report = ValidationReport(total_files=len(records))
        
        # Track for duplicate detection
        md5_to_paths: Dict[str, List[str]] = {}
        filename_to_paths: Dict[str, List[str]] = {}
        
        # Track valid years and categories seen
        years_seen: Set[int] = set()
        categories_seen: Set[str] = set()
        
        # Process each record
        for record in records:
            file_path = self.root_path / record.path
            
            # Track MD5 duplicates
            if record.md5:
                if record.md5 not in md5_to_paths:
                    md5_to_paths[record.md5] = []
                md5_to_paths[record.md5].append(record.path)
            
            # Track filename duplicates
            filename = Path(record.path).name
            if filename not in filename_to_paths:
                filename_to_paths[filename] = []
            filename_to_paths[filename].append(record.path)
            
            # Check for iCloud placeholders (size 0, no hash)
            if record.size_bytes == 0 and record.md5 is None:
                report.issues.append(ValidationIssue(
                    level="warning",
                    message="iCloud placeholder detected (file not downloaded)",
                    path=record.path
                ))
            
            # Track years and categories
            if record.year:
                years_seen.add(record.year)
            if record.category:
                categories_seen.add(record.category)
            
            # Check for orphan files (no year or category)
            if record.year is None and record.category is None:
                # Check if it's in a valid structure
                parts = Path(record.path).parts
                if len(parts) > 0 and parts[0] not in ["metadata", ".DS_Store", "Thumbs.db"]:
                    report.issues.append(ValidationIssue(
                        level="error",
                        message="Orphan file: not in any year/category folder",
                        path=record.path
                    ))
            
            # Check for invalid year folder
            if record.year:
                if record.year < 1900 or record.year > 2100:
                    report.issues.append(ValidationIssue(
                        level="error",
                        message=f"Invalid year: {record.year}",
                        path=record.path
                    ))
            
            # Check for invalid category
            if record.category and record.category not in ALLOWED_CATEGORIES:
                report.issues.append(ValidationIssue(
                    level="warning",
                    message=f"Unknown category: {record.category}",
                    path=record.path
                ))
            
            # Check for misplaced files
            self._check_misplaced(record, report)
        
        # Check for MD5 duplicates
        for md5_hash, paths in md5_to_paths.items():
            if len(paths) > 1:
                report.issues.append(ValidationIssue(
                    level="warning",
                    message=f"Duplicate files (same MD5): {', '.join(paths)}",
                    path=paths[0]
                ))
        
        # Check for filename duplicates across different folders
        for filename, paths in filename_to_paths.items():
            if len(paths) > 1:
                # Check if they're in different directories
                dirs = set(str(Path(p).parent) for p in paths)
                if len(dirs) > 1:
                    report.issues.append(ValidationIssue(
                        level="warning",
                        message=f"Duplicate filename '{filename}' in multiple locations: {', '.join(paths)}",
                        path=paths[0]
                    ))
        
        # Set overall validity (only errors make it invalid)
        error_count = sum(1 for issue in report.issues if issue.level == "error")
        report.valid = error_count == 0
        
        return report
    
    def _is_excluded(self, file_path: Path) -> bool:
        """Check if a file is under an excluded top-level directory.
        
        Files under directories in EXCLUDED_TOP_LEVEL_DIRS are completely
        skipped during validation. This prevents metadata, version control,
        and build artifact directories from appearing as orphans.
        
        Only checks top-level directories relative to root_path. Nested
        directories with similar names are not automatically excluded.
        
        Args:
            file_path: Absolute path to file
            
        Returns:
            True if file is under an excluded directory
        
        Examples:
            root/metadata/file.txt -> True (excluded)
            root/2024/receipts/file.txt -> False (not excluded)
            root/2024/metadata/file.txt -> False (only top-level excluded)
        """
        try:
            rel_path = file_path.relative_to(self.root_path)
            
            # Check if first path component is in excluded set
            if rel_path.parts:
                top_level_dir = rel_path.parts[0]
                return top_level_dir in EXCLUDED_TOP_LEVEL_DIRS
                
        except ValueError:
            # Path is not relative to root_path
            pass
        
        return False
    
    def _infer_year(self, file_path: Path) -> int | None:
        """Infer tax year from file path.
        
        Looks for 4-digit year (YYYY) in path components.
        Also handles "Personal" folder as a special case (returns None).
        
        Args:
            file_path: Path to file
            
        Returns:
            Year as integer, or None if not found
        """
        parts = file_path.parts
        
        for part in parts:
            # Check for 4-digit year
            if re.match(r'^\d{4}$', part):
                year = int(part)
                # Sanity check
                if 1900 <= year <= 2100:
                    return year
            
            # Check for "Personal" folder
            if part.lower() == "personal":
                return None
        
        return None
    
    def _infer_category(self, file_path: Path) -> str | None:
        """Infer category from file path.
        
        Looks for known category folder names in path.
        
        Args:
            file_path: Path to file
            
        Returns:
            Category name, or None if not found
        """
        parts = file_path.parts
        
        for part in parts:
            part_lower = part.lower()
            
            # Check against allowed categories
            if part_lower in ALLOWED_CATEGORIES:
                return part_lower
            
            # Check for common variations
            if "receipt" in part_lower:
                return "receipts"
            if "statement" in part_lower and "bank" in part_lower:
                return "bank_statements"
            if "statement" in part_lower:
                return "statements"
            if "invoice" in part_lower:
                return "invoices"
        
        return None
    
    def _compute_md5(self, file_path: Path) -> str | None:
        """Compute MD5 hash of file in streaming, chunked fashion.
        
        Uses 8KB chunks to avoid loading large files into memory.
        Caches results to avoid recomputation.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash as hex string, or None if unreadable
        """
        path_str = str(file_path)
        
        # Check cache first
        if path_str in self._hash_cache:
            return self._hash_cache[path_str]
        
        try:
            md5_hash = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                # Read in 8KB chunks
                while chunk := f.read(8192):
                    md5_hash.update(chunk)
            
            result = md5_hash.hexdigest()
            
            # Cache result
            self._hash_cache[path_str] = result
            
            return result
            
        except (OSError, IOError, PermissionError):
            # File unreadable - return None
            return None
    
    def _check_misplaced(self, record: TaxFileRecord, report: ValidationReport) -> None:
        """Check if a file is misplaced (wrong year or category).
        
        A file is misplaced if:
        - It has a year in filename but is in wrong year folder
        - It's clearly a receipt but not in receipts folder
        - It's a bank statement but not in statements folder
        
        Args:
            record: File record to check
            report: Validation report to add issues to
        """
        filename = Path(record.path).name.lower()
        
        # Check for year mismatch in filename
        year_match = re.search(r'(19|20)\d{2}', filename)
        if year_match:
            filename_year = int(year_match.group())
            if record.year and filename_year != record.year:
                report.issues.append(ValidationIssue(
                    level="warning",
                    message=f"File contains year {filename_year} but is in {record.year} folder",
                    path=record.path
                ))
        
        # Check for category mismatch
        if "receipt" in filename and record.category != "receipts":
            report.issues.append(ValidationIssue(
                level="warning",
                message=f"File appears to be a receipt but is in '{record.category}' folder",
                path=record.path
            ))
        
        if "statement" in filename and "bank" in filename:
            if record.category not in ["bank_statements", "statements"]:
                report.issues.append(ValidationIssue(
                    level="warning",
                    message=f"File appears to be a bank statement but is in '{record.category}' folder",
                    path=record.path
                ))
        
        if "invoice" in filename and record.category != "invoices":
            report.issues.append(ValidationIssue(
                level="warning",
                message=f"File appears to be an invoice but is in '{record.category}' folder",
                path=record.path
            ))

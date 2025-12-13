"""Tax archive sync module.

Synchronizes tax archive structure by moving files to canonical locations.
Detects duplicates and prepares safe sync plans.
See TAX_SYNC_IMPLEMENTATION.md for specifications.
"""

from pathlib import Path
from typing import Dict, List, Set, Optional
import shutil
import hashlib

from .tax_models import TaxFileRecord, SyncPlan, SyncResult
from .tax_validator import TaxValidator


class TaxSync:
    """Synchronizes tax archive to canonical structure.
    
    Analyzes archive structure and creates plans to move files into their
    canonical locations (YYYY/category/filename.ext). Handles duplicates
    safely and provides dry-run capability.
    
    Canonical structure:
        {root_path}/YYYY/category/filename.ext
    
    Where:
        - YYYY is a 4-digit year (1900-2100)
        - category is one of the allowed categories
        - filename.ext is the original filename
    
    Safe defaults:
        - Never deletes files without explicit safe_delete=True
        - Always operates as dry-run unless explicitly disabled
        - Accumulates all errors without stopping execution
        - Recomputes MD5 after each operation
    """
    
    def __init__(self, root_path: Path, safe_delete: bool = False):
        """Initialize tax archive synchronizer.
        
        Args:
            root_path: Root directory of tax archive to synchronize
            safe_delete: If True, allow deletion of duplicates/orphans (default: False)
        """
        self.root_path = Path(root_path)
        self.safe_delete = safe_delete
        self._validator = TaxValidator(root_path)
    
    def plan(self) -> SyncPlan:
        """Create synchronization plan for tax archive.
        
        Analyzes current archive structure and determines what operations
        are needed to achieve canonical structure:
        
        1. Scans all files using TaxValidator
        2. Identifies files not in canonical locations
        3. Detects duplicates by MD5 hash
        4. Chooses canonical winner for duplicates (newest file preferred)
        5. Prepares lists of operations:
           - to_copy: Files to move to canonical location
           - to_update: Files in correct location but with metadata differences
           - to_delete: Duplicates/orphans (only if safe_delete enabled)
        
        Canonical location logic:
            - Must have both year and category
            - Must be in path: {root_path}/{year}/{category}/{filename}
            - Exact path match required
        
        Duplicate resolution:
            - Newest file wins (by modification time)
            - If same mtime, alphabetically first path wins
            - Winner stays, losers marked for deletion (if safe_delete)
        
        Returns:
            SyncPlan with all planned operations
        """
        # Scan archive to get all file records
        records = self._validator.scan()
        
        # Initialize plan
        plan = SyncPlan()
        
        # Track canonical locations and duplicates
        canonical_locations: Dict[str, TaxFileRecord] = {}  # canonical_path -> record
        md5_to_records: Dict[str, List[TaxFileRecord]] = {}  # md5 -> [records]
        
        # Group records by MD5 for duplicate detection
        for record in records:
            if record.md5:
                if record.md5 not in md5_to_records:
                    md5_to_records[record.md5] = []
                md5_to_records[record.md5].append(record)
        
        # Process each file
        for record in records:
            # Try to infer missing year from filename if we have a category
            if record.year is None and record.category is not None:
                inferred_year = self._infer_year_from_filename(record.path)
                if inferred_year:
                    # Create updated record with inferred year
                    record = TaxFileRecord(
                        path=record.path,
                        year=inferred_year,
                        category=record.category,
                        size_bytes=record.size_bytes,
                        md5=record.md5
                    )
            
            # Skip files without year or category (true orphans)
            if record.year is None or record.category is None:
                continue
            
            # Determine canonical path
            canonical_path = self._get_canonical_path(record)
            
            # Check if file is already in canonical location
            is_canonical = self._is_canonical(record)
            
            if is_canonical:
                # File is in correct location
                canonical_locations[canonical_path] = record
            else:
                # File needs to be moved to canonical location
                
                # Check if canonical location already exists
                if canonical_path in canonical_locations:
                    # Conflict: another file already in canonical location
                    existing = canonical_locations[canonical_path]
                    
                    # Compare files to decide which to keep
                    if self._should_replace(record, existing):
                        # New file should replace existing
                        plan.to_update.append(record)
                        canonical_locations[canonical_path] = record
                    # else: existing file is better, ignore new file
                else:
                    # No conflict, plan to copy file to canonical location
                    plan.to_copy.append(record)
                    canonical_locations[canonical_path] = record
        
        # Handle duplicates (same MD5)
        if self.safe_delete:
            for md5_hash, duplicate_records in md5_to_records.items():
                if len(duplicate_records) > 1:
                    # Multiple files with same content
                    
                    # Choose canonical winner
                    winner = self._choose_duplicate_winner(duplicate_records)
                    
                    # Mark losers for deletion
                    for record in duplicate_records:
                        if record.path != winner.path:
                            # Only delete if not already in to_copy or to_update
                            if not any(r.path == record.path for r in plan.to_copy):
                                if not any(r.path == record.path for r in plan.to_update):
                                    plan.to_delete.append(record.path)
        
        return plan
    
    def apply(self, plan: SyncPlan, *, dry_run: bool = True) -> SyncResult:
        """Apply synchronization plan to tax archive.
        
        Executes planned operations to move files into canonical structure.
        
        Operations performed:
            1. to_copy: Move files to canonical locations
            2. to_update: Replace files at canonical locations
            3. to_delete: Remove duplicate/orphan files (if safe_delete enabled)
        
        Safety features:
            - Dry-run by default (must explicitly set dry_run=False)
            - All filesystem operations wrapped in try/except
            - Errors accumulated without stopping execution
            - MD5 recomputed after each move/update
            - Creates parent directories as needed
            - Preserves file metadata (timestamps, permissions)
        
        File operations:
            - Uses shutil.move() for moving files
            - Uses shutil.copy2() for updating (preserves metadata)
            - Creates directories with parents=True, exist_ok=True
        
        Args:
            plan: SyncPlan with operations to execute
            dry_run: If True, only simulate operations (default: True)
        
        Returns:
            SyncResult with operation counts and any errors encountered
        """
        result = SyncResult()
        
        # Process to_copy operations
        for record in plan.to_copy:
            try:
                source_path = self.root_path / record.path
                canonical_path = self._get_canonical_path(record)
                dest_path = self.root_path / canonical_path
                
                if dry_run:
                    # Simulate operation
                    result.copied += 1
                else:
                    # Ensure destination directory exists
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file to canonical location
                    shutil.move(str(source_path), str(dest_path))
                    
                    # Recompute MD5 after move
                    self._recompute_md5(dest_path)
                    
                    result.copied += 1
                    
            except (OSError, IOError, PermissionError, shutil.Error) as e:
                error_msg = f"Failed to copy {record.path}: {str(e)}"
                result.errors.append(error_msg)
        
        # Process to_update operations
        for record in plan.to_update:
            try:
                source_path = self.root_path / record.path
                canonical_path = self._get_canonical_path(record)
                dest_path = self.root_path / canonical_path
                
                if dry_run:
                    # Simulate operation
                    result.updated += 1
                else:
                    # Ensure destination directory exists
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Backup existing file if it exists
                    if dest_path.exists():
                        backup_path = dest_path.with_suffix(dest_path.suffix + '.backup')
                        shutil.move(str(dest_path), str(backup_path))
                    
                    try:
                        # Move new file to canonical location
                        shutil.move(str(source_path), str(dest_path))
                        
                        # Recompute MD5 after update
                        self._recompute_md5(dest_path)
                        
                        # Remove backup if successful
                        if backup_path.exists():
                            backup_path.unlink()
                        
                        result.updated += 1
                        
                    except Exception as e:
                        # Restore backup on failure
                        if backup_path.exists():
                            shutil.move(str(backup_path), str(dest_path))
                        raise
                    
            except (OSError, IOError, PermissionError, shutil.Error) as e:
                error_msg = f"Failed to update {record.path}: {str(e)}"
                result.errors.append(error_msg)
        
        # Process to_delete operations
        for path_str in plan.to_delete:
            try:
                file_path = self.root_path / path_str
                
                if dry_run:
                    # Simulate operation
                    result.deleted += 1
                else:
                    # Only delete if safe_delete is enabled
                    if self.safe_delete:
                        if file_path.exists():
                            file_path.unlink()
                            result.deleted += 1
                    else:
                        error_msg = f"Skipped deletion (safe_delete disabled): {path_str}"
                        result.errors.append(error_msg)
                    
            except (OSError, IOError, PermissionError) as e:
                error_msg = f"Failed to delete {path_str}: {str(e)}"
                result.errors.append(error_msg)
        
        return result
    
    def _get_canonical_path(self, record: TaxFileRecord) -> str:
        """Compute canonical path for a file record.
        
        Canonical format: {year}/{category}/{filename}
        
        Args:
            record: File record with year, category, and path
            
        Returns:
            Canonical path string relative to root
        """
        if record.year is None or record.category is None:
            # Cannot compute canonical path without year and category
            return record.path
        
        filename = Path(record.path).name
        canonical = f"{record.year}/{record.category}/{filename}"
        
        return canonical
    
    def _is_canonical(self, record: TaxFileRecord) -> bool:
        """Check if a file is already in its canonical location.
        
        A file is canonical if its path exactly matches: {year}/{category}/{filename}
        
        Args:
            record: File record to check
            
        Returns:
            True if file is in canonical location
        """
        if record.year is None or record.category is None:
            return False
        
        canonical_path = self._get_canonical_path(record)
        
        # Normalize paths for comparison
        actual_path = Path(record.path).as_posix()
        canonical_normalized = Path(canonical_path).as_posix()
        
        return actual_path == canonical_normalized
    
    def _should_replace(self, new_record: TaxFileRecord, existing_record: TaxFileRecord) -> bool:
        """Decide if new file should replace existing file at canonical location.
        
        Comparison logic:
            1. Prefer file with MD5 hash over file without
            2. Prefer newer file (by modification time)
            3. If same mtime, prefer larger file
            4. If same size, prefer alphabetically first path
        
        Args:
            new_record: New file record
            existing_record: Existing file record at canonical location
            
        Returns:
            True if new file should replace existing
        """
        # Prefer files with MD5 hash
        if new_record.md5 and not existing_record.md5:
            return True
        if existing_record.md5 and not new_record.md5:
            return False
        
        # Get file modification times
        try:
            new_path = self.root_path / new_record.path
            existing_path = self.root_path / existing_record.path
            
            new_mtime = new_path.stat().st_mtime if new_path.exists() else 0
            existing_mtime = existing_path.stat().st_mtime if existing_path.exists() else 0
            
            # Prefer newer file
            if new_mtime > existing_mtime:
                return True
            elif existing_mtime > new_mtime:
                return False
                
        except (OSError, IOError):
            pass
        
        # Prefer larger file
        if new_record.size_bytes > existing_record.size_bytes:
            return True
        elif existing_record.size_bytes > new_record.size_bytes:
            return False
        
        # Tie-breaker: alphabetically first path
        return new_record.path < existing_record.path
    
    def _choose_duplicate_winner(self, records: List[TaxFileRecord]) -> TaxFileRecord:
        """Choose canonical winner from duplicate files.
        
        Selection logic:
            1. Prefer file already in canonical location
            2. Prefer file with both year and category
            3. Prefer newer file (by modification time)
            4. If same mtime, prefer larger file
            5. If same size, prefer alphabetically first path
        
        Args:
            records: List of duplicate file records (same MD5)
            
        Returns:
            Winning file record
        """
        if not records:
            raise ValueError("Cannot choose winner from empty list")
        
        if len(records) == 1:
            return records[0]
        
        # Prefer files already in canonical location
        canonical_records = [r for r in records if self._is_canonical(r)]
        if canonical_records:
            records = canonical_records
            if len(records) == 1:
                return records[0]
        
        # Prefer files with both year and category
        complete_records = [r for r in records if r.year is not None and r.category is not None]
        if complete_records:
            records = complete_records
            if len(records) == 1:
                return records[0]
        
        # Sort by modification time (newest first)
        def get_mtime(record: TaxFileRecord) -> float:
            try:
                path = self.root_path / record.path
                return path.stat().st_mtime if path.exists() else 0
            except (OSError, IOError):
                return 0
        
        sorted_by_mtime = sorted(records, key=get_mtime, reverse=True)
        
        # Check if top candidates have same mtime
        top_mtime = get_mtime(sorted_by_mtime[0])
        same_mtime = [r for r in sorted_by_mtime if get_mtime(r) == top_mtime]
        
        if len(same_mtime) == 1:
            return same_mtime[0]
        
        # Tie-break by size (largest first)
        sorted_by_size = sorted(same_mtime, key=lambda r: r.size_bytes, reverse=True)
        
        if sorted_by_size[0].size_bytes > sorted_by_size[1].size_bytes:
            return sorted_by_size[0]
        
        # Final tie-break: alphabetically first path
        return sorted(sorted_by_size, key=lambda r: r.path)[0]
    
    def _infer_year_from_filename(self, path_str: str) -> Optional[int]:
        """Infer year from filename when not present in folder structure.
        
        Looks for 4-digit year (YYYY) in filename.
        
        Args:
            path_str: Path to file
            
        Returns:
            Year as integer, or None if not found
        """
        import re
        
        filename = Path(path_str).name
        
        # Look for 4-digit year in filename
        match = re.search(r'(19|20)\d{2}', filename)
        if match:
            year = int(match.group())
            if 1900 <= year <= 2100:
                return year
        
        return None
    
    def _recompute_md5(self, file_path: Path) -> Optional[str]:
        """Recompute MD5 hash of a file after move/update.
        
        Uses streaming computation to handle large files safely.
        
        Args:
            file_path: Path to file to hash
            
        Returns:
            MD5 hash as hex string, or None if computation fails
        """
        try:
            md5_hash = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    md5_hash.update(chunk)
            
            return md5_hash.hexdigest()
            
        except (OSError, IOError, PermissionError):
            return None

"""Tax-related models.

Data models for tax archive validation and synchronization.
See TAX_VALIDATOR_IMPLEMENTATION.md and TAX_SYNC_IMPLEMENTATION.md for specifications.
"""

from typing import Literal
from pydantic import BaseModel, Field


class TaxFileRecord(BaseModel):
    """Represents a single file in the tax archive.
    
    Used by both validator and sync modules to track file metadata.
    Follows naming conventions specified in TAX_VALIDATOR_IMPLEMENTATION.md.
    
    Attributes:
        path: Full or relative path to the file
        year: Tax year extracted from path/filename (None if not parseable)
        category: File category (receipts, statements, etc.) extracted from path
        size_bytes: File size in bytes
        md5: MD5 hash of file contents (None if not computed)
    """
    path: str
    year: int | None = None
    category: str | None = None
    size_bytes: int = Field(ge=0)
    md5: str | None = None


class ValidationIssue(BaseModel):
    """Represents a single validation issue found during tax archive validation.
    
    Used by ValidationReport to track problems found in the archive.
    Implements severity levels as specified in TAX_VALIDATOR_IMPLEMENTATION.md.
    
    Attributes:
        level: Severity level - "error" for critical issues, "warning" for non-critical
        message: Human-readable description of the issue
        path: Path to the file or directory where the issue was found
    """
    level: Literal["error", "warning"]
    message: str
    path: str


class ValidationReport(BaseModel):
    """Aggregated results of tax archive validation.
    
    Contains all issues found during validation and summary statistics.
    Implements validation rules from TAX_VALIDATOR_IMPLEMENTATION.md.
    
    Attributes:
        issues: List of all validation issues found (errors and warnings)
        total_files: Total number of files scanned
        valid: True if no errors found (warnings are acceptable)
    """
    issues: list[ValidationIssue] = Field(default_factory=list)
    total_files: int = Field(ge=0, default=0)
    valid: bool = True

    def summary(self) -> str:
        """Generate a human-readable summary of the validation report.
        
        Returns:
            Multi-line string summarizing validation results including:
            - Total files scanned
            - Number of errors and warnings
            - Overall validation status
        """
        error_count = sum(1 for issue in self.issues if issue.level == "error")
        warning_count = sum(1 for issue in self.issues if issue.level == "warning")
        
        status = "VALID" if self.valid else "INVALID"
        lines = [
            f"Validation Status: {status}",
            f"Total Files: {self.total_files}",
            f"Errors: {error_count}",
            f"Warnings: {warning_count}"
        ]
        return "\n".join(lines)


class SyncPlan(BaseModel):
    """Plan for synchronizing tax archives between source and destination.
    
    Computed by comparing source and destination archives before execution.
    Implements sync planning logic from TAX_SYNC_IMPLEMENTATION.md.
    
    Attributes:
        to_copy: Files that exist in source but not in destination
        to_delete: Paths in destination that should be removed (not in source)
        to_update: Files that exist in both but differ (by size or hash)
    """
    to_copy: list[TaxFileRecord] = Field(default_factory=list)
    to_delete: list[str] = Field(default_factory=list)
    to_update: list[TaxFileRecord] = Field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if the sync plan contains any actions.
        
        Returns:
            True if no files need to be copied, deleted, or updated
        """
        return (
            len(self.to_copy) == 0 
            and len(self.to_delete) == 0 
            and len(self.to_update) == 0
        )


class SyncResult(BaseModel):
    """Results of executing a tax archive synchronization.
    
    Tracks the outcome of applying a SyncPlan.
    Implements result tracking from TAX_SYNC_IMPLEMENTATION.md.
    
    Attributes:
        copied: Number of files successfully copied
        deleted: Number of files/directories successfully deleted
        updated: Number of files successfully updated
        errors: List of error messages encountered during sync
    """
    copied: int = Field(ge=0, default=0)
    deleted: int = Field(ge=0, default=0)
    updated: int = Field(ge=0, default=0)
    errors: list[str] = Field(default_factory=list)

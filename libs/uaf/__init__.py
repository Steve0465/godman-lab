"""
Unified Archive Framework (UAF)

A modular, extensible framework for managing and validating any type of archive.
"""

from .base_archive import BaseArchive
from .archive_validator import ArchiveValidator, ArchiveValidationResult
from .archive_sync import sync_archive, regenerate_manifest, regenerate_hash_index
from .archive_scoring import calculate_integrity_score
from .archive_factory import create_archive
from .registry import register_archive, get_archive, list_archives

__all__ = [
    "BaseArchive",
    "ArchiveValidator",
    "ArchiveValidationResult",
    "sync_archive",
    "regenerate_manifest",
    "regenerate_hash_index",
    "calculate_integrity_score",
    "create_archive",
    "register_archive",
    "get_archive",
    "list_archives",
]

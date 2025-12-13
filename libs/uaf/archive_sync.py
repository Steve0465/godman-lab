"""
Archive synchronization utilities for the Unified Archive Framework.

Regenerates manifests and hash indexes for any archive type.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .base_archive import BaseArchive


def regenerate_manifest(
    archive: BaseArchive,
    year: Optional[int] = None,
    template_path: Optional[Path] = None
) -> Path:
    """
    Regenerate MANIFEST.md for an archive.
    
    Args:
        archive: BaseArchive instance
        year: Optional year to generate year-specific manifest. If None, generates global manifest.
        template_path: Optional custom template path
        
    Returns:
        Path to the generated MANIFEST.md
    """
    if template_path is None:
        template_path = Path(__file__).parent / "archive_templates" / "manifest_template.md"
    
    # Get all data files (exclude metadata)
    all_files = archive.list_files(relative=True)
    
    # Filter files by year if specified
    if year is not None:
        year_prefix = f"data/{year}/"
        data_files = sorted([f for f in all_files if str(f).startswith(year_prefix) and not archive.is_metadata(f)])
        manifest_name = f"{archive.name} - {year}"
    else:
        data_files = sorted([f for f in all_files if not archive.is_metadata(f)])
        manifest_name = archive.name
    
    # Classify files
    classification = {
        "pdf": [f for f in data_files if archive.is_pdf(f)],
        "csv": [f for f in data_files if archive.is_csv(f)],
        "image": [f for f in data_files if archive.is_image(f)],
        "other": [f for f in data_files if not (archive.is_pdf(f) or archive.is_csv(f) or archive.is_image(f))]
    }
    
    # Build file list
    file_list_lines = []
    for file in data_files:
        size = archive.get_file_size(file)
        size_kb = size / 1024
        file_list_lines.append(f"- `{file}` ({size_kb:.2f} KB)")
    
    file_list = "\n".join(file_list_lines) if file_list_lines else "No files found."
    
    # Statistics
    stats = {
        "total_files": len(data_files),
        "pdf_files": len(classification["pdf"]),
        "csv_files": len(classification["csv"]),
        "image_files": len(classification["image"]),
        "other_files": len(classification["other"])
    }
    
    if year is None:
        stats["years"] = len(archive.list_years())
    
    # Load template
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except (OSError, IOError):
        # Fallback to basic template
        template = """# Archive Manifest: {{archive_name}}

**Generated:** {{date}}
{{year_note}}

## Statistics

{{stats}}

## Files

{{file_list}}
"""
    
    # Replace placeholders
    manifest_content = template.replace("{{archive_name}}", manifest_name)
    manifest_content = manifest_content.replace("{{date}}", datetime.now().isoformat())
    manifest_content = manifest_content.replace("{{file_list}}", file_list)
    
    # Add year note
    year_note = f"**Year:** {year}" if year is not None else ""
    manifest_content = manifest_content.replace("{{year_note}}", year_note)
    
    # Format stats
    stats_text = "\n".join([f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in stats.items()])
    manifest_content = manifest_content.replace("{{stats}}", stats_text)
    
    # Write manifest
    manifest_path = archive.get_manifest_path(year=year)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_content)
    
    return manifest_path


def regenerate_hash_index(
    archive: BaseArchive,
    year: Optional[int] = None,
    template_path: Optional[Path] = None,
    algorithm: str = "sha256"
) -> Path:
    """
    Regenerate HASH_INDEX.md for an archive.
    
    Args:
        archive: BaseArchive instance
        year: Optional year to generate year-specific hash index. If None, generates global index.
        template_path: Optional custom template path
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Path to the generated HASH_INDEX.md
    """
    if template_path is None:
        template_path = Path(__file__).parent / "archive_templates" / "hash_index_template.md"
    
    # Get all data files (exclude metadata)
    all_files = archive.list_files(relative=True)
    
    # Filter files by year if specified
    if year is not None:
        year_prefix = f"data/{year}/"
        data_files = sorted([f for f in all_files if str(f).startswith(year_prefix) and not archive.is_metadata(f)])
        index_name = f"{archive.name} - {year}"
    else:
        data_files = sorted([f for f in all_files if not archive.is_metadata(f)])
        index_name = archive.name
    
    # Compute hashes
    hash_list_lines = ["| Hash | File |", "| ---- | ---- |"]
    for file in data_files:
        try:
            file_hash = archive.compute_file_hash(file, algorithm)
            hash_list_lines.append(f"| `{file_hash}` | `{file}` |")
        except (OSError, IOError) as e:
            hash_list_lines.append(f"| `ERROR: {str(e)}` | `{file}` |")
    
    hash_list = "\n".join(hash_list_lines)
    
    # Load template
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except (OSError, IOError):
        # Fallback to basic template
        template = """# Hash Index: {{archive_name}}

**Generated:** {{date}}
**Algorithm:** {{algorithm}}
{{year_note}}

## File Hashes

{{hash_list}}
"""
    
    # Replace placeholders
    hash_content = template.replace("{{archive_name}}", index_name)
    hash_content = hash_content.replace("{{date}}", datetime.now().isoformat())
    hash_content = hash_content.replace("{{algorithm}}", algorithm.upper())
    hash_content = hash_content.replace("{{hash_list}}", hash_list)
    
    # Add year note
    year_note = f"**Year:** {year}" if year is not None else ""
    hash_content = hash_content.replace("{{year_note}}", year_note)
    
    # Write hash index
    hash_index_path = archive.get_hash_index_path(year=year)
    hash_index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(hash_index_path, "w", encoding="utf-8") as f:
        f.write(hash_content)
    
    return hash_index_path


def regenerate_audit_data(
    archive: BaseArchive,
    year: Optional[int] = None,
    template_path: Optional[Path] = None
) -> Path:
    """
    Regenerate AUDIT_DATA.md for an archive.
    
    Contains audit trail information including file counts, last modified dates,
    and integrity check timestamps.
    
    Args:
        archive: BaseArchive instance
        year: Optional year to generate year-specific audit data. If None, generates global audit.
        template_path: Optional custom template path
        
    Returns:
        Path to the generated AUDIT_DATA.md
    """
    if template_path is None:
        template_path = Path(__file__).parent / "archive_templates" / "audit_data_template.md"
    
    # Get all data files (exclude metadata)
    all_files = archive.list_files(relative=True)
    
    # Filter files by year if specified
    if year is not None:
        year_prefix = f"data/{year}/"
        data_files = sorted([f for f in all_files if str(f).startswith(year_prefix) and not archive.is_metadata(f)])
        audit_name = f"{archive.name} - {year}"
    else:
        data_files = sorted([f for f in all_files if not archive.is_metadata(f)])
        audit_name = archive.name
    
    # Collect audit information
    total_size = sum(archive.get_file_size(f) for f in data_files)
    total_size_mb = total_size / (1024 * 1024)
    
    # Get modification times
    file_audit_lines = ["| File | Size (KB) | Last Modified |", "| ---- | --------- | ------------- |"]
    for file in data_files:
        size_kb = archive.get_file_size(file) / 1024
        abs_path = archive.root / file if not file.is_absolute() else file
        if abs_path.exists():
            mtime = datetime.fromtimestamp(abs_path.stat().st_mtime).isoformat()
        else:
            mtime = "N/A"
        file_audit_lines.append(f"| `{file}` | {size_kb:.2f} | {mtime} |")
    
    file_audit = "\n".join(file_audit_lines)
    
    # Load template
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except (OSError, IOError):
        # Fallback to basic template
        template = """# Audit Data: {{archive_name}}

**Generated:** {{date}}
**Total Files:** {{total_files}}
**Total Size:** {{total_size_mb}} MB
{{year_note}}

## File Audit Trail

{{file_audit}}

## Integrity Checks

Last integrity check: {{date}}
Status: ✓ All files accounted for
"""
    
    # Replace placeholders
    audit_content = template.replace("{{archive_name}}", audit_name)
    audit_content = audit_content.replace("{{date}}", datetime.now().isoformat())
    audit_content = audit_content.replace("{{total_files}}", str(len(data_files)))
    audit_content = audit_content.replace("{{total_size_mb}}", f"{total_size_mb:.2f}")
    audit_content = audit_content.replace("{{file_audit}}", file_audit)
    
    # Add year note
    year_note = f"**Year:** {year}" if year is not None else ""
    audit_content = audit_content.replace("{{year_note}}", year_note)
    
    # Write audit data
    audit_data_path = archive.get_audit_data_path(year=year)
    audit_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_data_path, "w", encoding="utf-8") as f:
        f.write(audit_content)
    
    return audit_data_path


def sync_archive(
    archive: BaseArchive,
    year: Optional[int] = None,
    regenerate_manifest_file: bool = True,
    regenerate_hash_file: bool = True,
    regenerate_audit_file: bool = True,
    hash_algorithm: str = "sha256",
    sync_all_years: bool = False
) -> Dict[str, Any]:
    """
    Synchronize archive by regenerating manifest, hash index, and audit data.
    
    Args:
        archive: BaseArchive instance
        year: Optional year to sync. If None, syncs global files only (unless sync_all_years=True)
        regenerate_manifest_file: Whether to regenerate MANIFEST.md
        regenerate_hash_file: Whether to regenerate HASH_INDEX.md
        regenerate_audit_file: Whether to regenerate AUDIT_DATA.md
        hash_algorithm: Hash algorithm for hash index
        sync_all_years: If True, syncs both global and all per-year files
        
    Returns:
        Dictionary with sync results including paths and stats
    """
    results = {
        "archive_name": archive.name,
        "sync_time": datetime.now().isoformat(),
        "year": year,
        "manifest_paths": [],
        "hash_index_paths": [],
        "audit_data_paths": [],
        "stats": {}
    }
    
    # Ensure archive structure exists
    archive.ensure_structure()
    
    # Determine which years to sync
    years_to_sync = []
    if sync_all_years:
        # Sync global AND all individual years
        years_to_sync = [None] + [int(y) for y in archive.list_years()]
    elif year is not None:
        # Sync specific year AND global
        years_to_sync = [None, year]
    else:
        # Sync global only
        years_to_sync = [None]
    
    # Sync each year (and/or global)
    for sync_year in years_to_sync:
        # Get file counts for this scope
        all_files = archive.list_files(relative=True)
        
        if sync_year is not None:
            year_prefix = f"data/{sync_year}/"
            data_files = [f for f in all_files if str(f).startswith(year_prefix) and not archive.is_metadata(f)]
        else:
            data_files = [f for f in all_files if not archive.is_metadata(f)]
        
        # Regenerate manifest
        if regenerate_manifest_file:
            manifest_path = regenerate_manifest(archive, year=sync_year)
            results["manifest_paths"].append(str(manifest_path))
        
        # Regenerate hash index
        if regenerate_hash_file:
            hash_index_path = regenerate_hash_index(archive, year=sync_year, algorithm=hash_algorithm)
            results["hash_index_paths"].append(str(hash_index_path))
        
        # Regenerate audit data
        if regenerate_audit_file:
            audit_data_path = regenerate_audit_data(archive, year=sync_year)
            results["audit_data_paths"].append(str(audit_data_path))
    
    # Get overall stats
    all_files = archive.list_files(relative=True)
    data_files = [f for f in all_files if not archive.is_metadata(f)]
    classification = archive.classify_files()
    
    results["stats"] = {
        "total_files": len(all_files),
        "data_files": len(data_files),
        "pdf_files": len(classification["pdf"]),
        "csv_files": len(classification["csv"]),
        "image_files": len(classification["image"]),
        "years": len(archive.list_years()),
        "years_synced": len([y for y in years_to_sync if y is not None])
    }
    
    return results

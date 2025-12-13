# Unified Archive Framework (UAF)

A modular, extensible framework for managing and validating any type of archive with production-grade code, comprehensive type hints, and detailed docstrings.

## Overview

The UAF provides a consistent, archive-agnostic interface for:
- Creating and managing structured file archives
- Validating archive integrity with scoring
- Synchronizing metadata (manifests and hash indexes)
- Detecting corruption (zero-byte files, hash mismatches, missing files)
- Registering and accessing multiple archives

## Architecture

```
libs/uaf/
├── base_archive.py           # Core BaseArchive class
├── archive_validator.py      # Validation and integrity checking
├── archive_sync.py           # Metadata regeneration
├── archive_scoring.py        # Integrity scoring logic
├── archive_factory.py        # Archive creation utilities
├── registry.py               # Central archive registry
└── archive_templates/        # Template files
    ├── readme_template.md
    ├── manifest_template.md
    └── hash_index_template.md
```

## Key Features

### 1. Archive-Agnostic Design
No domain-specific logic - works with any archive type (tax documents, photos, datasets, etc.)

### 2. Integrity Scoring
Deducts points only for real corruption:
- **-5 points** per zero-byte file
- **-3 points** per hash mismatch
- **-2 points** per missing file

Documentation issues generate warnings only (no score deduction).

### 3. Comprehensive Validation
- Filesystem scanning
- Zero-byte file detection
- Manifest comparison
- Hash verification (SHA-256)
- Detailed reporting

### 4. Template-Based Generation
Uses customizable templates for:
- README.md
- MANIFEST.md
- HASH_INDEX.md

## Quick Start

### Creating a New Archive

```python
from libs.uaf import create_archive
from pathlib import Path

# Create a new archive
archive = create_archive(
    name="my_archive",
    root=Path("/path/to/archive"),
    auto_register=True
)
```

### Loading an Existing Archive

```python
from libs.uaf import BaseArchive
from pathlib import Path

archive = BaseArchive(
    root=Path("/path/to/archive"),
    name="my_archive"
)
```

### Validating an Archive

```python
from libs.uaf import ArchiveValidator

validator = ArchiveValidator(archive)
result = validator.validate(check_hashes=True)

print(f"Integrity Score: {result.integrity_score}/100")
print(f"Completeness: {result.completeness_score}%")
print(f"Health Status: {result.is_healthy}")

# Print full report
print(result)
```

### Synchronizing Metadata

```python
from libs.uaf import sync_archive

# Regenerate MANIFEST.md and HASH_INDEX.md
result = sync_archive(archive)

print(f"Manifest: {result['manifest_path']}")
print(f"Hash Index: {result['hash_index_path']}")
print(f"Stats: {result['stats']}")
```

### Using the Registry

```python
from libs.uaf import register_archive, get_archive, list_archives

# Register an archive
register_archive("my_archive", Path("/path/to/archive"))

# Get a registered archive
archive = get_archive("my_archive")

# List all registered archives
archives = list_archives()
for a in archives:
    print(f"{a['name']}: {a['path']}")
```

## Archive Structure

Each archive follows a consistent structure:

```
my_archive/
├── data/              # Archive data files
│   ├── 2023/         # Optional year-based organization
│   ├── 2024/
│   └── ...
├── metadata/         # Archive metadata
│   ├── MANIFEST.md   # File inventory
│   └── HASH_INDEX.md # SHA-256 hashes
└── README.md         # Archive documentation
```

## API Reference

### BaseArchive

Core archive class with common operations:

```python
class BaseArchive:
    def __init__(self, root: Path, name: str, config: Optional[Dict] = None)
    def ensure_structure() -> None
    def list_files(relative: bool = True) -> List[Path]
    def list_years() -> List[str]
    def classify_files() -> Dict[str, List[Path]]
    def compute_file_hash(path: Path, algorithm: str = "sha256") -> str
    def get_file_size(path: Path) -> int
    def is_pdf(path: Path) -> bool
    def is_csv(path: Path) -> bool
    def is_image(path: Path) -> bool
    def is_metadata(path: Path) -> bool
```

### ArchiveValidator

Validates archive integrity:

```python
class ArchiveValidator:
    def __init__(self, archive: BaseArchive)
    def validate(check_hashes: bool = True) -> ArchiveValidationResult
```

### ArchiveValidationResult

Validation results:

```python
@dataclass
class ArchiveValidationResult:
    archive_name: str
    validation_time: str
    stats: Dict[str, Any]
    integrity_score: int
    completeness_score: float
    critical_problems: List[str]
    warnings: List[str]
    zero_byte_files: List[str]
    hash_mismatches: List[str]
    missing_files: List[str]
    extra_files: List[str]
    manifest_exists: bool
    hash_index_exists: bool
    is_healthy: bool
```

### Functions

**Archive Creation:**
- `create_archive(name, root, config=None, auto_register=True) -> BaseArchive`

**Synchronization:**
- `sync_archive(archive, regenerate_manifest=True, regenerate_hash=True) -> Dict`
- `regenerate_manifest(archive, template_path=None) -> Path`
- `regenerate_hash_index(archive, template_path=None, algorithm="sha256") -> Path`

**Scoring:**
- `calculate_integrity_score(zero_byte_files, hash_mismatches, missing_files) -> Dict`
- `calculate_completeness_score(expected, actual, missing) -> Dict`

**Registry:**
- `register_archive(name, path) -> None`
- `unregister_archive(name) -> bool`
- `get_archive(name, config=None) -> Optional[BaseArchive]`
- `list_archives() -> List[Dict]`
- `archive_exists(name) -> bool`
- `load_from_config(config_path) -> int`
- `save_to_config(config_path) -> None`

## Examples

### Example 1: Photo Archive

```python
from libs.uaf import create_archive, sync_archive, ArchiveValidator
from pathlib import Path

# Create photo archive
archive = create_archive("photos_2024", Path("~/Photos/Archive"))

# Add photos to data directory
# ... copy files to archive.root / "data" ...

# Sync metadata
sync_archive(archive)

# Validate
validator = ArchiveValidator(archive)
result = validator.validate()
print(result)
```

### Example 2: Dataset Archive

```python
from libs.uaf import BaseArchive, sync_archive

# Load existing dataset
archive = BaseArchive(
    root=Path("/datasets/ml_models"),
    name="ml_dataset_v1"
)

# Classify files
classification = archive.classify_files()
print(f"CSVs: {len(classification['csv'])}")
print(f"Images: {len(classification['image'])}")

# Regenerate hash index only
from libs.uaf import regenerate_hash_index
regenerate_hash_index(archive)
```

### Example 3: Multi-Archive Management

```python
from libs.uaf import register_archive, list_archives, get_archive
from pathlib import Path

# Register multiple archives
register_archive("photos", Path("~/Photos/Archive"))
register_archive("documents", Path("~/Documents/Archive"))
register_archive("datasets", Path("/data/archives"))

# List all
for archive_info in list_archives():
    print(f"{archive_info['name']}: {archive_info['path']}")
    
    # Validate each
    archive = get_archive(archive_info['name'])
    validator = ArchiveValidator(archive)
    result = validator.validate(check_hashes=False)  # Skip hash check for speed
    print(f"  Score: {result.integrity_score}/100")
```

## Configuration

Archives can be configured with custom settings:

```python
config = {
    "description": "My custom archive",
    "version": "1.0",
    "custom_field": "value"
}

archive = BaseArchive(
    root=Path("/path/to/archive"),
    name="my_archive",
    config=config
)

# Access config
print(archive.config["description"])
```

## Extending the Framework

### Custom Archive Types

Subclass `BaseArchive` for domain-specific logic:

```python
from libs.uaf import BaseArchive
from pathlib import Path

class TaxArchive(BaseArchive):
    def list_tax_years(self) -> List[str]:
        return self.list_years()
    
    def get_receipts(self) -> List[Path]:
        return [f for f in self.list_files() if "receipt" in str(f).lower()]
```

### Custom Templates

Provide custom templates to `regenerate_manifest()`:

```python
from libs.uaf import regenerate_manifest

custom_template = Path("my_templates/custom_manifest.md")
regenerate_manifest(archive, template_path=custom_template)
```

### Custom Scoring

Use `ScoringConfig` for custom penalties:

```python
from libs.uaf.archive_scoring import calculate_integrity_score, ScoringConfig

config = ScoringConfig(
    max_score=100,
    zero_byte_penalty=10,  # Stricter
    hash_mismatch_penalty=5,
    missing_file_penalty=3
)

result = calculate_integrity_score(
    zero_byte_files=zero_files,
    hash_mismatches=mismatches,
    missing_files=missing,
    config=config
)
```

## Best Practices

1. **Always sync after adding files**: Run `sync_archive()` after modifying archive contents
2. **Validate regularly**: Schedule periodic validation to detect corruption early
3. **Use the registry**: Register frequently-used archives for easy access
4. **Check hashes selectively**: Hash verification is slow; use `check_hashes=False` for quick scans
5. **Backup metadata**: Keep copies of MANIFEST.md and HASH_INDEX.md external to the archive

## Integration with Existing Code

The UAF is designed to work alongside existing archive tools like `tax_archive_validator` and `tax_archive_sync`. Simply import the base classes and reuse the common infrastructure:

```python
# Before: Tax-specific implementation
from scripts.tax_archive_sync import regenerate_manifest

# After: Unified implementation
from libs.uaf import BaseArchive, regenerate_manifest

archive = BaseArchive(root=tax_root, name="tax_archive")
regenerate_manifest(archive)
```

## License

Part of the godman-lab project.

"""
Base Archive class for the Unified Archive Framework.

Provides core functionality for any archive type without domain-specific logic.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib


class BaseArchive:
    """
    Archive-agnostic base class for managing structured file archives.
    
    Provides common operations for archive management including structure creation,
    file listing, and classification helpers.
    """
    
    def __init__(self, root: Path, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a BaseArchive instance.
        
        Args:
            root: Root directory path of the archive
            name: Name identifier for the archive
            config: Optional configuration dictionary for archive-specific settings
        """
        self.root = Path(root)
        self.name = name
        self.config = config or {}
    
    def ensure_structure(self) -> None:
        """
        Create the basic archive directory structure.
        
        Creates:
            - root directory
            - metadata/ subdirectory
            - data/ subdirectory
        """
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "metadata").mkdir(exist_ok=True)
        (self.root / "data").mkdir(exist_ok=True)
    
    def list_files(self, relative: bool = True) -> List[Path]:
        """
        List all files in the archive recursively.
        
        Args:
            relative: If True, return paths relative to archive root. If False, return absolute paths.
            
        Returns:
            List of Path objects for all files in the archive
        """
        if not self.root.exists():
            return []
        
        files = []
        for item in self.root.rglob("*"):
            if item.is_file():
                if relative:
                    files.append(item.relative_to(self.root))
                else:
                    files.append(item)
        return sorted(files)
    
    def list_years(self) -> List[str]:
        """
        List top-level year folders in the data directory.
        
        Returns:
            Sorted list of year folder names (e.g., ['2023', '2024'])
        """
        data_dir = self.root / "data"
        if not data_dir.exists():
            return []
        
        years = []
        for item in data_dir.iterdir():
            if item.is_dir() and item.name.isdigit() and len(item.name) == 4:
                years.append(item.name)
        
        return sorted(years)
    
    def get_manifest_path(self, year: Optional[int] = None) -> Path:
        """
        Get the path to the MANIFEST.md file.
        
        Args:
            year: Optional year to get year-specific manifest. If None, returns global manifest.
        
        Returns:
            Path object for MANIFEST.md in the metadata directory or year directory
        """
        if year is not None:
            # Year-specific manifest
            return self.root / "data" / str(year) / "MANIFEST.md"
        else:
            # Global manifest
            return self.root / "metadata" / "MANIFEST.md"
    
    def get_hash_index_path(self, year: Optional[int] = None) -> Path:
        """
        Get the path to the HASH_INDEX.md file.
        
        Args:
            year: Optional year to get year-specific hash index. If None, returns global index.
        
        Returns:
            Path object for HASH_INDEX.md in the metadata directory or year directory
        """
        if year is not None:
            # Year-specific hash index
            return self.root / "data" / str(year) / "HASH_INDEX.md"
        else:
            # Global hash index
            return self.root / "metadata" / "HASH_INDEX.md"
    
    def get_audit_data_path(self, year: Optional[int] = None) -> Path:
        """
        Get the path to the AUDIT_DATA.md file.
        
        Args:
            year: Optional year to get year-specific audit data. If None, returns global audit data.
        
        Returns:
            Path object for AUDIT_DATA.md in the metadata directory or year directory
        """
        if year is not None:
            # Year-specific audit data
            return self.root / "data" / str(year) / "AUDIT_DATA.md"
        else:
            # Global audit data
            return self.root / "metadata" / "AUDIT_DATA.md"
    
    def is_pdf(self, path: Path) -> bool:
        """
        Check if a file is a PDF.
        
        Args:
            path: Path to check
            
        Returns:
            True if the file has a .pdf extension
        """
        return path.suffix.lower() == ".pdf"
    
    def is_csv(self, path: Path) -> bool:
        """
        Check if a file is a CSV.
        
        Args:
            path: Path to check
            
        Returns:
            True if the file has a .csv extension
        """
        return path.suffix.lower() == ".csv"
    
    def is_image(self, path: Path) -> bool:
        """
        Check if a file is an image.
        
        Args:
            path: Path to check
            
        Returns:
            True if the file has a common image extension
        """
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
        return path.suffix.lower() in image_extensions
    
    def is_metadata(self, path: Path) -> bool:
        """
        Check if a file is in the metadata directory.
        
        Args:
            path: Path to check (relative to archive root)
            
        Returns:
            True if the file is under the metadata directory
        """
        try:
            # Check if the path starts with 'metadata'
            parts = path.parts
            return len(parts) > 0 and parts[0] == "metadata"
        except (ValueError, IndexError):
            return False
    
    def classify_files(self) -> Dict[str, List[Path]]:
        """
        Classify all files in the archive by type.
        
        Returns:
            Dictionary with keys: 'pdf', 'csv', 'image', 'metadata', 'other'
            Each key maps to a list of relative Path objects
        """
        files = self.list_files(relative=True)
        
        classification = {
            "pdf": [],
            "csv": [],
            "image": [],
            "metadata": [],
            "other": []
        }
        
        for file in files:
            if self.is_metadata(file):
                classification["metadata"].append(file)
            elif self.is_pdf(file):
                classification["pdf"].append(file)
            elif self.is_csv(file):
                classification["csv"].append(file)
            elif self.is_image(file):
                classification["image"].append(file)
            else:
                classification["other"].append(file)
        
        return classification
    
    def compute_file_hash(self, path: Path, algorithm: str = "sha256") -> str:
        """
        Compute the hash of a file.
        
        Args:
            path: Path to the file (can be relative or absolute)
            algorithm: Hash algorithm to use (default: sha256)
            
        Returns:
            Hexadecimal hash string
        """
        if not path.is_absolute():
            path = self.root / path
        
        hash_obj = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def get_file_size(self, path: Path) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            path: Path to the file (can be relative or absolute)
            
        Returns:
            File size in bytes
        """
        if not path.is_absolute():
            path = self.root / path
        
        return path.stat().st_size if path.exists() else 0
    
    def __repr__(self) -> str:
        """String representation of the archive."""
        return f"BaseArchive(name='{self.name}', root='{self.root}')"

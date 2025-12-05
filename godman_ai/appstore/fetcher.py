"""
Skill Fetcher

Downloads .godmanskill archives from remote URLs with validation.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SkillFetcher:
    """
    Downloads and validates skill archives.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the fetcher.
        
        Args:
            cache_dir: Directory for temporary downloads
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".godman" / "tmp"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, url: str, expected_sha256: Optional[str] = None) -> Path:
        """
        Download a .godmanskill file from URL.
        
        Args:
            url: Download URL
            expected_sha256: Optional SHA256 hash for validation
        
        Returns:
            Path to downloaded file
        
        Raises:
            ValueError: If download fails or validation fails
        """
        # Lazy import
        try:
            import requests
        except ImportError:
            import urllib.request
            requests = None
        
        # Extract filename from URL
        filename = url.split("/")[-1]
        if not filename.endswith(".godmanskill"):
            filename += ".godmanskill"
        
        dest_path = self.cache_dir / filename
        
        logger.info(f"Downloading skill from {url}")
        
        try:
            if requests:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                # Fallback to urllib
                urllib.request.urlretrieve(url, dest_path)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise ValueError(f"Failed to download skill: {e}")
        
        # Validate file size
        file_size = dest_path.stat().st_size
        if file_size == 0:
            dest_path.unlink()
            raise ValueError("Downloaded file is empty")
        
        logger.debug(f"Downloaded {file_size} bytes to {dest_path}")
        
        # Validate checksum if provided
        if expected_sha256:
            actual_sha256 = self._compute_sha256(dest_path)
            if actual_sha256 != expected_sha256:
                dest_path.unlink()
                raise ValueError(
                    f"Checksum mismatch: expected {expected_sha256}, "
                    f"got {actual_sha256}"
                )
            logger.debug("Checksum validated")
        
        logger.info(f"Skill downloaded successfully: {dest_path}")
        return dest_path
    
    def _compute_sha256(self, path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def cleanup(self):
        """Remove all cached downloads."""
        for file in self.cache_dir.glob("*.godmanskill"):
            try:
                file.unlink()
                logger.debug(f"Removed cached file: {file}")
            except Exception as e:
                logger.warning(f"Failed to remove {file}: {e}")

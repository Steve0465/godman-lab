"""Tests for diag_report.py script."""

import pytest
import sys
from pathlib import Path
import tempfile

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from diag_report import find_related_photos


def test_find_related_photos_by_dtc():
    """Test finding photos by DTC code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        photo_dir = Path(tmpdir)
        
        # Create test photo files
        (photo_dir / 'P0300_before.jpg').touch()
        (photo_dir / 'P0300_after.jpg').touch()
        (photo_dir / 'P0420_sensor.jpg').touch()
        (photo_dir / 'random_photo.jpg').touch()
        
        # Find photos for P0300
        photos = find_related_photos(photo_dir, dtc='P0300')
        
        assert len(photos) == 2
        assert any('P0300_before' in str(p) for p in photos)
        assert any('P0300_after' in str(p) for p in photos)
        assert not any('P0420' in str(p) for p in photos)


def test_find_related_photos_by_job_id():
    """Test finding photos by job ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        photo_dir = Path(tmpdir)
        
        # Create test photo files
        (photo_dir / 'job123_step1.jpg').touch()
        (photo_dir / 'job123_step2.jpg').touch()
        (photo_dir / 'job456_other.jpg').touch()
        
        # Find photos for job123
        photos = find_related_photos(photo_dir, job_id='job123')
        
        assert len(photos) == 2
        assert all('job123' in str(p) for p in photos)


def test_find_related_photos_case_insensitive():
    """Test that photo search is case insensitive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        photo_dir = Path(tmpdir)
        
        # Create photo with uppercase extension
        (photo_dir / 'P0300_repair.JPG').touch()
        (photo_dir / 'P0300_test.jpeg').touch()
        
        photos = find_related_photos(photo_dir, dtc='P0300')
        
        assert len(photos) == 2


def test_find_related_photos_empty_directory():
    """Test finding photos in empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        photo_dir = Path(tmpdir)
        
        photos = find_related_photos(photo_dir, dtc='P0300')
        
        assert len(photos) == 0

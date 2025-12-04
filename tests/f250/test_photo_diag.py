"""
Tests for photo indexing and diagnostic report functionality
"""
import pytest
import sys
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from f250.scripts.diag_report import (
    find_related_photos,
    analyze_dtc
)


def test_find_related_photos_by_dtc(temp_dir):
    """Test finding photos by DTC code."""
    photos_dir = temp_dir / 'photos'
    photos_dir.mkdir()
    
    # Create test photo files with DTC codes in names
    (photos_dir / 'p0301_spark_plug.jpg').touch()
    (photos_dir / '0301_cylinder1.jpg').touch()
    (photos_dir / 'engine_bay.jpg').touch()
    (photos_dir / 'p0302_issue.jpg').touch()
    
    # Find photos for P0301
    photos = find_related_photos(photos_dir, dtc='P0301')
    
    assert len(photos) == 2, "Should find 2 photos matching P0301"
    photo_names = [p.name for p in photos]
    assert 'p0301_spark_plug.jpg' in photo_names
    assert '0301_cylinder1.jpg' in photo_names


def test_find_related_photos_by_job_name(temp_dir):
    """Test finding photos by job name."""
    photos_dir = temp_dir / 'photos'
    photos_dir.mkdir()
    
    # Create test photo files with job names
    (photos_dir / 'spark_plug_replacement_1.jpg').touch()
    (photos_dir / 'spark_plug_replacement_2.jpg').touch()
    (photos_dir / 'oil_change.jpg').touch()
    
    # Find photos for spark plug job
    photos = find_related_photos(photos_dir, job_name='spark_plug')
    
    assert len(photos) == 2, "Should find 2 photos matching spark_plug"


def test_find_related_photos_non_dtc_prefixes(temp_dir):
    """Test photo finding with C, B, U DTC prefixes."""
    photos_dir = temp_dir / 'photos'
    photos_dir.mkdir()
    
    # Create photos with different DTC prefix types
    (photos_dir / 'c1234_chassis.jpg').touch()
    (photos_dir / 'b5678_body.jpg').touch()
    (photos_dir / 'u9012_network.jpg').touch()
    
    # Test each prefix type
    photos_c = find_related_photos(photos_dir, dtc='C1234')
    assert len(photos_c) == 1
    
    photos_b = find_related_photos(photos_dir, dtc='B5678')
    assert len(photos_b) == 1
    
    photos_u = find_related_photos(photos_dir, dtc='U9012')
    assert len(photos_u) == 1


def test_analyze_dtc_powertrain():
    """Test DTC analysis for powertrain codes."""
    analysis = analyze_dtc('P0301')
    
    assert 'Powertrain' in analysis
    assert 'Generic' in analysis
    assert 'MISFIRE' in analysis
    assert 'Cylinder 1' in analysis


def test_analyze_dtc_chassis():
    """Test DTC analysis for chassis codes."""
    analysis = analyze_dtc('C1234')
    
    assert 'Chassis' in analysis


def test_analyze_dtc_body():
    """Test DTC analysis for body codes."""
    analysis = analyze_dtc('B5678')
    
    assert 'Body' in analysis


def test_analyze_dtc_network():
    """Test DTC analysis for network codes."""
    analysis = analyze_dtc('U9012')
    
    assert 'Network' in analysis or 'Communication' in analysis


def test_analyze_dtc_random_misfire():
    """Test DTC analysis for random misfire."""
    analysis = analyze_dtc('P0300')
    
    assert 'MISFIRE' in analysis
    assert 'Random' in analysis or 'Multiple' in analysis


def test_analyze_dtc_invalid():
    """Test DTC analysis with invalid code."""
    analysis = analyze_dtc('XYZ')
    
    assert 'Invalid' in analysis


def test_photo_index_append(temp_dir, sample_photo_path):
    """Test appending photos to photo directory."""
    photos_dir = temp_dir / 'photos'
    photos_dir.mkdir()
    
    # Copy sample photo with descriptive name
    dest = photos_dir / 'p0301_test_photo.jpg'
    shutil.copy(sample_photo_path, dest)
    
    assert dest.exists()
    
    # Verify it can be found
    photos = find_related_photos(photos_dir, dtc='P0301')
    assert len(photos) == 1
    assert photos[0].name == 'p0301_test_photo.jpg'

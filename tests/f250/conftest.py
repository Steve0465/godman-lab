"""
Test fixtures for F250 tests
"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp(prefix='f250_test_')
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def sample_csv_path():
    """Path to sample OBD CSV file."""
    return Path(__file__).parent / 'fixtures' / 'sample_obd.csv'


@pytest.fixture
def sample_photo_path():
    """Path to sample photo file."""
    return Path(__file__).parent / 'fixtures' / 'sample_photo.jpg'


@pytest.fixture
def test_db_path(temp_dir):
    """Path to test database."""
    return temp_dir / 'test.db'


@pytest.fixture
def test_csv_dir(temp_dir, sample_csv_path):
    """Create test CSV directory with sample file."""
    csv_dir = temp_dir / 'obd_csv'
    csv_dir.mkdir()
    # Copy sample CSV to temp directory
    shutil.copy(sample_csv_path, csv_dir / 'sample.csv')
    return csv_dir


@pytest.fixture
def test_maintenance_csv(temp_dir):
    """Path to test maintenance CSV."""
    return temp_dir / 'maintenance.csv'

"""
Unit tests for bubble segmentation module.
"""

import pytest
from pathlib import Path
import sys

# Add prototype to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from prototype.enhanced.segmentation import BubbleSegmenter, BubbleBoundingBox


@pytest.fixture
def test_image():
    """Get path to test image."""
    examples_dir = Path(__file__).parent.parent.parent / "examples"
    return str(examples_dir / "test_image1.png")


def test_bubble_segmenter_init():
    """Test BubbleSegmenter initialization."""
    segmenter = BubbleSegmenter(preset='imessage')
    assert segmenter.preset == 'imessage'
    assert segmenter.config['min_area'] > 0


def test_bubble_segmenter_invalid_preset():
    """Test BubbleSegmenter with invalid preset."""
    with pytest.raises(ValueError):
        BubbleSegmenter(preset='invalid')


def test_segment_image_detects_bubbles(test_image):
    """Test that segmentation detects at least one bubble."""
    segmenter = BubbleSegmenter(preset='imessage')
    bubbles = segmenter.segment_image(test_image)
    
    # Should detect at least one bubble in test image
    assert len(bubbles) >= 1, "Should detect at least one bubble"
    
    # Check bubble properties
    for bubble in bubbles:
        assert isinstance(bubble, BubbleBoundingBox)
        assert bubble.width > 0
        assert bubble.height > 0
        assert 0 <= bubble.confidence <= 1


def test_segment_image_invalid_path():
    """Test segmentation with invalid image path."""
    segmenter = BubbleSegmenter()
    
    with pytest.raises(ValueError):
        segmenter.segment_image("nonexistent.png")


def test_bubble_bounding_box_to_dict():
    """Test BubbleBoundingBox to_dict method."""
    bubble = BubbleBoundingBox(x=10, y=20, width=100, height=50, confidence=0.95)
    
    bubble_dict = bubble.to_dict()
    
    assert bubble_dict['x'] == 10
    assert bubble_dict['y'] == 20
    assert bubble_dict['width'] == 100
    assert bubble_dict['height'] == 50
    assert bubble_dict['confidence'] == 0.95


def test_bubble_sorting():
    """Test that bubbles are sorted by Y coordinate."""
    segmenter = BubbleSegmenter(preset='imessage')
    
    # Get test image with multiple bubbles
    examples_dir = Path(__file__).parent.parent.parent / "examples"
    test_image = str(examples_dir / "test_image1.png")
    
    bubbles = segmenter.segment_image(test_image)
    
    if len(bubbles) > 1:
        # Check that bubbles are sorted by Y
        for i in range(len(bubbles) - 1):
            assert bubbles[i].y <= bubbles[i + 1].y, "Bubbles should be sorted by Y coordinate"


def test_different_presets():
    """Test different messaging platform presets."""
    presets = ['imessage', 'whatsapp', 'android_sms']
    
    for preset in presets:
        segmenter = BubbleSegmenter(preset=preset)
        assert segmenter.preset == preset
        assert 'min_area' in segmenter.config
        assert 'max_area' in segmenter.config

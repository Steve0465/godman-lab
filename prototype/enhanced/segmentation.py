"""
Bubble segmentation module for detecting message bubbles in screenshots.

This module provides heuristic OpenCV-based bubble detection for common messaging UIs
(iMessage, WhatsApp, Android SMS). It exports per-bubble cropped images and bounding boxes.

Example usage:
    from prototype.enhanced.segmentation import BubbleSegmenter
    
    segmenter = BubbleSegmenter(preset='imessage')
    bubbles = segmenter.segment_image('screenshot.png')
    
    for i, bubble in enumerate(bubbles):
        bubble.save_crop(f'bubble_{i}.png')
"""

import cv2
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
import json


@dataclass
class BubbleBoundingBox:
    """Represents a detected message bubble with its bounding box."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    image_crop: Optional[np.ndarray] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'x': int(self.x),
            'y': int(self.y),
            'width': int(self.width),
            'height': int(self.height),
            'confidence': float(self.confidence)
        }
    
    def save_crop(self, output_path: str):
        """Save the cropped bubble image to a file."""
        if self.image_crop is not None:
            cv2.imwrite(output_path, self.image_crop)


class BubbleSegmenter:
    """
    Heuristic OpenCV-based bubble segmentation for messaging UIs.
    
    Supports configurable presets for different messaging platforms:
    - imessage: iOS iMessage interface
    - whatsapp: WhatsApp interface
    - android_sms: Android SMS/Messages interface
    """
    
    # Preset configurations for different messaging platforms
    PRESETS = {
        'imessage': {
            'min_area': 500,
            'max_area': 500000,
            'aspect_ratio_range': (0.1, 10.0),
            'blur_kernel': (5, 5),
            'canny_low': 30,
            'canny_high': 100,
            'min_contour_points': 4,
            'roundness_threshold': 0.3,
        },
        'whatsapp': {
            'min_area': 300,
            'max_area': 500000,
            'aspect_ratio_range': (0.1, 10.0),
            'blur_kernel': (5, 5),
            'canny_low': 40,
            'canny_high': 120,
            'min_contour_points': 4,
            'roundness_threshold': 0.25,
        },
        'android_sms': {
            'min_area': 400,
            'max_area': 500000,
            'aspect_ratio_range': (0.1, 10.0),
            'blur_kernel': (5, 5),
            'canny_low': 35,
            'canny_high': 110,
            'min_contour_points': 4,
            'roundness_threshold': 0.28,
        },
    }
    
    def __init__(self, preset: str = 'imessage', **kwargs):
        """
        Initialize the bubble segmenter.
        
        Args:
            preset: Platform preset name ('imessage', 'whatsapp', 'android_sms')
            **kwargs: Override preset parameters
        """
        if preset not in self.PRESETS:
            raise ValueError(f"Unknown preset '{preset}'. Available: {list(self.PRESETS.keys())}")
        
        self.config = self.PRESETS[preset].copy()
        self.config.update(kwargs)
        self.preset = preset
    
    def segment_image(self, image_path: str) -> List[BubbleBoundingBox]:
        """
        Detect message bubbles in an image.
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            List of BubbleBoundingBox objects representing detected bubbles
        """
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        return self._detect_bubbles(img)
    
    def _detect_bubbles(self, img: np.ndarray) -> List[BubbleBoundingBox]:
        """
        Internal method to detect bubbles using OpenCV contour detection.
        
        Args:
            img: Input image as numpy array
            
        Returns:
            List of detected bubbles
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, self.config['blur_kernel'], 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, self.config['canny_low'], self.config['canny_high'])
        
        # Morphological operations to close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bubbles = []
        for contour in contours:
            # Filter by contour properties
            area = cv2.contourArea(contour)
            if area < self.config['min_area'] or area > self.config['max_area']:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio
            aspect_ratio = float(w) / h if h > 0 else 0
            if not (self.config['aspect_ratio_range'][0] <= aspect_ratio <= self.config['aspect_ratio_range'][1]):
                continue
            
            # Calculate roundness (perimeter-based heuristic)
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                roundness = 4 * np.pi * area / (perimeter * perimeter)
            else:
                roundness = 0
            
            # Filter by minimum roundness
            if roundness < self.config['roundness_threshold']:
                continue
            
            # Extract cropped region
            crop = img[y:y+h, x:x+w].copy()
            
            # Confidence based on multiple factors
            confidence = min(1.0, roundness * 1.5)  # Simple heuristic
            
            bubble = BubbleBoundingBox(
                x=x, y=y, width=w, height=h,
                confidence=confidence,
                image_crop=crop
            )
            bubbles.append(bubble)
        
        # Sort bubbles by Y coordinate (top to bottom)
        bubbles.sort(key=lambda b: b.y)
        
        return bubbles


def process_folder(input_folder: str, output_folder: str, preset: str = 'imessage'):
    """
    Process a folder of screenshots and export detected bubbles.
    
    Args:
        input_folder: Path to folder containing screenshot images
        output_folder: Path to folder for output (bubbles and metadata)
        preset: Platform preset name
        
    Returns:
        Dictionary with processing statistics
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    segmenter = BubbleSegmenter(preset=preset)
    
    # Image extensions to process
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    stats = {
        'processed': 0,
        'total_bubbles': 0,
        'files': []
    }
    
    for image_file in input_path.iterdir():
        if image_file.suffix.lower() not in image_extensions:
            continue
        
        try:
            print(f"Processing {image_file.name}...")
            bubbles = segmenter.segment_image(str(image_file))
            
            # Create output subfolder for this image
            image_output = output_path / image_file.stem
            image_output.mkdir(exist_ok=True)
            
            # Save each bubble
            bubble_metadata = []
            for i, bubble in enumerate(bubbles):
                crop_filename = f"bubble_{i:03d}.png"
                bubble.save_crop(str(image_output / crop_filename))
                bubble_metadata.append({
                    'index': i,
                    'filename': crop_filename,
                    **bubble.to_dict()
                })
            
            # Save metadata JSON
            metadata = {
                'source_image': image_file.name,
                'preset': preset,
                'bubble_count': len(bubbles),
                'bubbles': bubble_metadata
            }
            
            with open(image_output / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            stats['processed'] += 1
            stats['total_bubbles'] += len(bubbles)
            stats['files'].append({
                'name': image_file.name,
                'bubbles': len(bubbles)
            })
            
            print(f"  -> Found {len(bubbles)} bubbles")
            
        except Exception as e:
            print(f"  -> Error processing {image_file.name}: {e}")
    
    # Save overall stats
    with open(output_path / 'processing_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats


if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Segment message bubbles from screenshots')
    parser.add_argument('input', help='Input folder containing screenshots')
    parser.add_argument('output', help='Output folder for bubbles and metadata')
    parser.add_argument('--preset', default='imessage', 
                        choices=['imessage', 'whatsapp', 'android_sms'],
                        help='Messaging platform preset')
    
    args = parser.parse_args()
    
    stats = process_folder(args.input, args.output, args.preset)
    print(f"\n=== Processing Complete ===")
    print(f"Processed: {stats['processed']} images")
    print(f"Total bubbles: {stats['total_bubbles']}")

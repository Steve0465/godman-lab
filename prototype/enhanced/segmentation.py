"""
Bubble segmentation module for detecting message bubbles in messaging app screenshots.

This module provides heuristic OpenCV-based segmentation to detect and extract
individual message bubbles from screenshots of common messaging UIs like iMessage,
WhatsApp, and Android SMS.

Example usage:
    from segmentation import BubbleSegmenter, MessageUIPreset
    
    segmenter = BubbleSegmenter(preset=MessageUIPreset.IMESSAGE)
    bubbles = segmenter.segment_image('screenshot.png')
    
    for i, bubble in enumerate(bubbles):
        bubble.save(f'bubble_{i}.png')
"""

import cv2
import numpy as np
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Optional
import json


class MessageUIPreset(Enum):
    """Preset configurations for different messaging UIs."""
    IMESSAGE = "imessage"
    WHATSAPP = "whatsapp"
    ANDROID_SMS = "android_sms"
    GENERIC = "generic"


@dataclass
class BubbleBox:
    """Represents a detected message bubble with its location and content."""
    x: int
    y: int
    width: int
    height: int
    image: np.ndarray
    confidence: float = 1.0
    
    def to_dict(self) -> dict:
        """Convert bubble box to dictionary (excluding image data)."""
        return {
            'x': int(self.x),
            'y': int(self.y),
            'width': int(self.width),
            'height': int(self.height),
            'confidence': float(self.confidence)
        }
    
    def save(self, output_path: str) -> None:
        """Save the bubble image to file."""
        cv2.imwrite(output_path, self.image)


class BubbleSegmenter:
    """
    Detects and segments message bubbles from messaging app screenshots.
    
    Uses OpenCV-based heuristics including:
    - Adaptive thresholding
    - Contour detection
    - Shape filtering based on aspect ratio and size
    - Color-based filtering for specific UI presets
    """
    
    def __init__(self, preset: MessageUIPreset = MessageUIPreset.GENERIC):
        """
        Initialize the bubble segmenter.
        
        Args:
            preset: The messaging UI preset to use for detection parameters
        """
        self.preset = preset
        self.config = self._get_config(preset)
    
    def _get_config(self, preset: MessageUIPreset) -> dict:
        """Get configuration parameters for the given preset."""
        configs = {
            MessageUIPreset.IMESSAGE: {
                'min_width': 80,
                'max_width': 800,
                'min_height': 30,
                'max_height': 600,
                'min_aspect': 0.1,
                'max_aspect': 8.0,
                'blue_range': ([90, 50, 50], [130, 255, 255]),  # HSV range for iMessage blue
                'gray_range': ([0, 0, 180], [180, 30, 240]),    # HSV range for gray bubbles
            },
            MessageUIPreset.WHATSAPP: {
                'min_width': 80,
                'max_width': 800,
                'min_height': 30,
                'max_height': 600,
                'min_aspect': 0.1,
                'max_aspect': 8.0,
                'green_range': ([35, 40, 40], [85, 255, 255]),  # WhatsApp green
                'white_range': ([0, 0, 200], [180, 30, 255]),   # White bubbles
            },
            MessageUIPreset.ANDROID_SMS: {
                'min_width': 80,
                'max_width': 800,
                'min_height': 30,
                'max_height': 600,
                'min_aspect': 0.1,
                'max_aspect': 8.0,
            },
            MessageUIPreset.GENERIC: {
                'min_width': 60,
                'max_width': 900,
                'min_height': 25,
                'max_height': 700,
                'min_aspect': 0.1,
                'max_aspect': 10.0,
            }
        }
        return configs.get(preset, configs[MessageUIPreset.GENERIC])
    
    def segment_image(self, image_path: str) -> List[BubbleBox]:
        """
        Segment message bubbles from an image.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            List of BubbleBox objects representing detected bubbles
        """
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Detect bubbles using multiple methods
        bubbles = []
        
        # Method 1: Contour-based detection
        contour_bubbles = self._detect_by_contours(img)
        bubbles.extend(contour_bubbles)
        
        # Method 2: Color-based detection (for specific presets)
        if self.preset in [MessageUIPreset.IMESSAGE, MessageUIPreset.WHATSAPP]:
            color_bubbles = self._detect_by_color(img)
            bubbles.extend(color_bubbles)
        
        # Remove duplicates and filter
        bubbles = self._filter_overlapping_bubbles(bubbles)
        bubbles = self._sort_bubbles_top_to_bottom(bubbles)
        
        return bubbles
    
    def _detect_by_contours(self, img: np.ndarray) -> List[BubbleBox]:
        """Detect bubbles using contour detection."""
        bubbles = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter based on size and aspect ratio
            if self._is_valid_bubble_size(w, h):
                bubble_img = img[y:y+h, x:x+w].copy()
                bubble = BubbleBox(x=x, y=y, width=w, height=h, image=bubble_img)
                bubbles.append(bubble)
        
        return bubbles
    
    def _detect_by_color(self, img: np.ndarray) -> List[BubbleBox]:
        """Detect bubbles using color-based segmentation."""
        bubbles = []
        
        # Convert to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Get color ranges from config
        color_ranges = []
        if 'blue_range' in self.config:
            color_ranges.append(self.config['blue_range'])
        if 'gray_range' in self.config:
            color_ranges.append(self.config['gray_range'])
        if 'green_range' in self.config:
            color_ranges.append(self.config['green_range'])
        if 'white_range' in self.config:
            color_ranges.append(self.config['white_range'])
        
        for lower, upper in color_ranges:
            # Create mask for this color range
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                if self._is_valid_bubble_size(w, h):
                    bubble_img = img[y:y+h, x:x+w].copy()
                    bubble = BubbleBox(x=x, y=y, width=w, height=h, image=bubble_img, confidence=0.9)
                    bubbles.append(bubble)
        
        return bubbles
    
    def _is_valid_bubble_size(self, width: int, height: int) -> bool:
        """Check if dimensions match expected bubble size."""
        if width < self.config['min_width'] or width > self.config['max_width']:
            return False
        if height < self.config['min_height'] or height > self.config['max_height']:
            return False
        
        aspect_ratio = width / height if height > 0 else 0
        if aspect_ratio < self.config['min_aspect'] or aspect_ratio > self.config['max_aspect']:
            return False
        
        return True
    
    def _filter_overlapping_bubbles(self, bubbles: List[BubbleBox], iou_threshold: float = 0.5) -> List[BubbleBox]:
        """Remove overlapping bubbles, keeping the one with higher confidence."""
        if len(bubbles) <= 1:
            return bubbles
        
        # Sort by confidence (descending)
        sorted_bubbles = sorted(bubbles, key=lambda b: b.confidence, reverse=True)
        
        filtered = []
        for bubble in sorted_bubbles:
            overlaps = False
            for kept_bubble in filtered:
                if self._compute_iou(bubble, kept_bubble) > iou_threshold:
                    overlaps = True
                    break
            
            if not overlaps:
                filtered.append(bubble)
        
        return filtered
    
    def _compute_iou(self, bubble1: BubbleBox, bubble2: BubbleBox) -> float:
        """Compute Intersection over Union between two bubbles."""
        x1_min, y1_min = bubble1.x, bubble1.y
        x1_max, y1_max = bubble1.x + bubble1.width, bubble1.y + bubble1.height
        
        x2_min, y2_min = bubble2.x, bubble2.y
        x2_max, y2_max = bubble2.x + bubble2.width, bubble2.y + bubble2.height
        
        # Compute intersection
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # Compute union
        area1 = bubble1.width * bubble1.height
        area2 = bubble2.width * bubble2.height
        union_area = area1 + area2 - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def _sort_bubbles_top_to_bottom(self, bubbles: List[BubbleBox]) -> List[BubbleBox]:
        """Sort bubbles from top to bottom (conversation order)."""
        return sorted(bubbles, key=lambda b: b.y)
    
    def process_folder(self, input_folder: str, output_folder: str) -> dict:
        """
        Process all images in a folder and export bubbles.
        
        Args:
            input_folder: Path to folder containing screenshots
            output_folder: Path to folder for output bubbles and metadata
            
        Returns:
            Dictionary with processing statistics
        """
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        stats = {
            'images_processed': 0,
            'total_bubbles': 0,
            'results': []
        }
        
        # Process each image
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        for img_file in input_path.iterdir():
            if img_file.suffix.lower() not in image_extensions:
                continue
            
            try:
                bubbles = self.segment_image(str(img_file))
                
                # Create output subfolder for this image
                img_output = output_path / img_file.stem
                img_output.mkdir(exist_ok=True)
                
                # Save each bubble
                bubble_data = []
                for i, bubble in enumerate(bubbles):
                    bubble_path = img_output / f"bubble_{i:03d}.png"
                    bubble.save(str(bubble_path))
                    bubble_data.append(bubble.to_dict())
                
                # Save metadata
                metadata = {
                    'source_image': img_file.name,
                    'num_bubbles': len(bubbles),
                    'bubbles': bubble_data
                }
                
                with open(img_output / 'metadata.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                stats['images_processed'] += 1
                stats['total_bubbles'] += len(bubbles)
                stats['results'].append({
                    'image': img_file.name,
                    'bubbles_detected': len(bubbles)
                })
                
            except Exception as e:
                print(f"Error processing {img_file.name}: {e}")
        
        # Save overall stats
        with open(output_path / 'processing_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        return stats


def main():
    """CLI interface for bubble segmentation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Segment message bubbles from screenshots')
    parser.add_argument('input', help='Input image or folder')
    parser.add_argument('output', help='Output folder for bubbles')
    parser.add_argument('--preset', choices=['imessage', 'whatsapp', 'android_sms', 'generic'],
                       default='generic', help='Messaging UI preset')
    
    args = parser.parse_args()
    
    # Map string to enum
    preset_map = {
        'imessage': MessageUIPreset.IMESSAGE,
        'whatsapp': MessageUIPreset.WHATSAPP,
        'android_sms': MessageUIPreset.ANDROID_SMS,
        'generic': MessageUIPreset.GENERIC
    }
    
    segmenter = BubbleSegmenter(preset=preset_map[args.preset])
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Process single image
        bubbles = segmenter.segment_image(str(input_path))
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, bubble in enumerate(bubbles):
            bubble.save(str(output_path / f"bubble_{i:03d}.png"))
        
        print(f"Detected {len(bubbles)} bubbles from {input_path.name}")
    else:
        # Process folder
        stats = segmenter.process_folder(str(input_path), args.output)
        print(f"Processed {stats['images_processed']} images")
        print(f"Total bubbles detected: {stats['total_bubbles']}")


if __name__ == '__main__':
    main()

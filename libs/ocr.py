"""OCR utilities for image and PDF processing."""
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv

load_dotenv()

POPPLER_PATH = os.getenv("POPPLER_PATH", None)
TESSERACT_CMD = os.getenv("TESSERACT_CMD", None)

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def ocr_image(img: Image.Image, lang: str = 'eng') -> str:
    """
    Extract text from a PIL Image using Tesseract OCR.
    
    Args:
        img: PIL Image object
        lang: Language code for OCR (default: 'eng')
    
    Returns:
        Extracted text as string
    """
    return pytesseract.image_to_string(img, lang=lang)


def ocr_pdf(pdf_path: Union[str, Path], max_pages: int = None) -> str:
    """
    Extract text from a PDF file using OCR.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to process (None = all)
    
    Returns:
        Combined text from all pages
    """
    pdf_path = Path(pdf_path)
    
    # Convert PDF to images
    kwargs = {"poppler_path": POPPLER_PATH} if POPPLER_PATH else {}
    if max_pages:
        kwargs["last_page"] = max_pages
    
    images = convert_from_path(str(pdf_path), **kwargs)
    
    # OCR each page
    text_parts = []
    for i, img in enumerate(images):
        page_text = ocr_image(img)
        text_parts.append(page_text)
    
    return "\n\n".join(text_parts)


def ocr_file(file_path: Union[str, Path], max_pages: int = None) -> str:
    """
    Extract text from an image or PDF file.
    
    Args:
        file_path: Path to image or PDF file
        max_pages: For PDFs, max pages to process
    
    Returns:
        Extracted text as string
    """
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == '.pdf':
        return ocr_pdf(file_path, max_pages=max_pages)
    else:
        # Handle image files
        img = Image.open(file_path)
        return ocr_image(img)


def extract_text_from_images(image_paths: List[Union[str, Path]]) -> str:
    """
    Extract and combine text from multiple image files.
    
    Args:
        image_paths: List of paths to image files
    
    Returns:
        Combined text from all images
    """
    texts = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            text = ocr_image(img)
            texts.append(text)
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
    
    return "\n\n".join(texts)

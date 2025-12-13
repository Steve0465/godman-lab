"""
Trello Attachment Extractor

Extracts and downloads attachments from Trello cards, specifically targeting
safety cover jobs for measurement extraction and analysis.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse, unquote

import requests

from libs.trello.client import TrelloClient


# Configure logging
logger = logging.getLogger(__name__)


def normalize_filename(card_name: str, attachment_name: str, index: int) -> str:
    """
    Generate a normalized, filesystem-safe filename.
    
    Args:
        card_name: The Trello card name
        attachment_name: The original attachment filename
        index: The attachment index (for uniqueness)
    
    Returns:
        A normalized filename suitable for filesystem use
    
    Example:
        >>> normalize_filename("Smith Pool - Safety Cover", "IMG_1234.jpg", 0)
        'smith_pool_safety_cover_0_IMG_1234.jpg'
    """
    # Clean card name
    clean_card = re.sub(r'[^\w\s-]', '', card_name.lower())
    clean_card = re.sub(r'[-\s]+', '_', clean_card).strip('_')
    
    # Extract extension from attachment
    ext = Path(attachment_name).suffix
    clean_attachment = Path(attachment_name).stem
    clean_attachment = re.sub(r'[^\w\s-]', '', clean_attachment)
    clean_attachment = re.sub(r'[-\s]+', '_', clean_attachment).strip('_')
    
    # Limit length to avoid filesystem issues
    max_card_len = 50
    max_attach_len = 50
    
    if len(clean_card) > max_card_len:
        clean_card = clean_card[:max_card_len]
    
    if len(clean_attachment) > max_attach_len:
        clean_attachment = clean_attachment[:max_attach_len]
    
    return f"{clean_card}_{index}_{clean_attachment}{ext}"


def is_safety_cover_list(list_name: str) -> bool:
    """
    Check if a list name corresponds to safety cover jobs.
    
    Args:
        list_name: The Trello list name
    
    Returns:
        True if the list is related to safety covers
    """
    return "safety cover" in list_name.lower()


def download_attachment(
    url: str,
    output_path: Path,
    trello_client: TrelloClient,
    timeout: int = 30
) -> bool:
    """
    Download an attachment from a URL.
    
    Args:
        url: The attachment URL
        output_path: Where to save the file
        trello_client: Authenticated Trello client
        timeout: Request timeout in seconds
    
    Returns:
        True if download succeeded, False otherwise
    """
    try:
        # Check if this is a Trello attachment URL
        parsed = urlparse(url)
        is_trello_url = 'trello' in parsed.netloc
        
        # Build request params
        params = {}
        if is_trello_url:
            # Add authentication for Trello attachments
            params['key'] = trello_client.api_key
            params['token'] = trello_client.token
        
        # Download with streaming to handle large files
        response = requests.get(url, params=params, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # Write to file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Downloaded: {output_path.name}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False


def extract_safety_cover_attachments(
    export_path: str,
    out_dir: str,
    trello_client: TrelloClient = None
) -> List[str]:
    """
    Extract and download all attachments from safety cover cards.
    
    This function:
    1. Loads the Trello export JSON
    2. Filters cards in lists related to safety covers
    3. Extracts all attachments from matching cards
    4. Downloads them with normalized filenames
    5. Returns paths to all downloaded files
    
    Args:
        export_path: Path to the Trello export JSON file
        out_dir: Directory where attachments should be saved
        trello_client: Authenticated TrelloClient instance (created if None)
    
    Returns:
        List of paths to successfully downloaded files
    
    Raises:
        FileNotFoundError: If export_path doesn't exist
        ValueError: If export JSON is malformed
        
    Example:
        >>> client = TrelloClient()
        >>> files = extract_safety_cover_attachments(
        ...     "exports/memphis_pool_board.json",
        ...     "data/safety_cover_measurements",
        ...     client
        ... )
        >>> print(f"Downloaded {len(files)} attachments")
    """
    # Validate inputs
    export_file = Path(export_path)
    if not export_file.exists():
        raise FileNotFoundError(f"Export file not found: {export_path}")
    
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Trello client if needed
    if trello_client is None:
        trello_client = TrelloClient()
    
    # Load export data
    logger.info(f"Loading Trello export from {export_path}")
    try:
        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in export file: {e}")
    
    # Validate structure
    if 'lists' not in data or 'cards' not in data:
        raise ValueError("Export JSON missing required 'lists' or 'cards' keys")
    
    # Build list ID -> name mapping
    list_map = {lst['id']: lst['name'] for lst in data['lists']}
    
    # Filter safety cover cards
    safety_cover_cards = []
    for card in data['cards']:
        list_id = card.get('idList')
        if list_id and list_id in list_map:
            list_name = list_map[list_id]
            if is_safety_cover_list(list_name):
                safety_cover_cards.append(card)
    
    logger.info(f"Found {len(safety_cover_cards)} safety cover cards")
    
    # Extract and download attachments
    downloaded_files = []
    total_attachments = 0
    
    for card in safety_cover_cards:
        card_name = card.get('name', 'Unnamed')
        attachments = card.get('attachments', [])
        
        if not attachments:
            logger.debug(f"No attachments for card: {card_name}")
            continue
        
        logger.info(f"Processing {len(attachments)} attachments from: {card_name}")
        
        for idx, attachment in enumerate(attachments):
            total_attachments += 1
            
            # Get attachment URL
            url = attachment.get('url')
            if not url:
                logger.warning(f"Attachment missing URL in card: {card_name}")
                continue
            
            # Generate normalized filename
            original_name = attachment.get('name', 'attachment.jpg')
            normalized_name = normalize_filename(card_name, original_name, idx)
            output_path = output_dir / normalized_name
            
            # Skip if already exists
            if output_path.exists():
                logger.info(f"Skipping existing file: {normalized_name}")
                downloaded_files.append(str(output_path))
                continue
            
            # Download
            if download_attachment(url, output_path, trello_client):
                downloaded_files.append(str(output_path))
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Extraction Summary:")
    logger.info(f"  Cards processed: {len(safety_cover_cards)}")
    logger.info(f"  Total attachments: {total_attachments}")
    logger.info(f"  Successfully downloaded: {len(downloaded_files)}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info(f"{'='*60}\n")
    
    return downloaded_files


def extract_attachments_by_list_pattern(
    export_path: str,
    out_dir: str,
    list_pattern: str,
    trello_client: TrelloClient = None
) -> List[str]:
    """
    Extract attachments from cards in lists matching a pattern.
    
    More flexible version of extract_safety_cover_attachments that accepts
    any list name pattern.
    
    Args:
        export_path: Path to the Trello export JSON file
        out_dir: Directory where attachments should be saved
        list_pattern: Case-insensitive substring to match in list names
        trello_client: Authenticated TrelloClient instance (created if None)
    
    Returns:
        List of paths to successfully downloaded files
    
    Example:
        >>> # Extract liner installation measurements
        >>> files = extract_attachments_by_list_pattern(
        ...     "exports/memphis_pool_board.json",
        ...     "data/liner_measurements",
        ...     "liner"
        ... )
    """
    # This is basically the same as extract_safety_cover_attachments
    # but with a configurable pattern
    
    export_file = Path(export_path)
    if not export_file.exists():
        raise FileNotFoundError(f"Export file not found: {export_path}")
    
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if trello_client is None:
        trello_client = TrelloClient()
    
    # Load export
    logger.info(f"Loading Trello export from {export_path}")
    with open(export_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Build mapping
    list_map = {lst['id']: lst['name'] for lst in data['lists']}
    
    # Filter cards by pattern
    pattern_lower = list_pattern.lower()
    matching_cards = []
    
    for card in data['cards']:
        list_id = card.get('idList')
        if list_id and list_id in list_map:
            list_name = list_map[list_id]
            if pattern_lower in list_name.lower():
                matching_cards.append(card)
    
    logger.info(f"Found {len(matching_cards)} cards matching pattern '{list_pattern}'")
    
    # Download attachments
    downloaded_files = []
    total_attachments = 0
    
    for card in matching_cards:
        card_name = card.get('name', 'Unnamed')
        attachments = card.get('attachments', [])
        
        if not attachments:
            continue
        
        logger.info(f"Processing {len(attachments)} attachments from: {card_name}")
        
        for idx, attachment in enumerate(attachments):
            total_attachments += 1
            url = attachment.get('url')
            
            if not url:
                continue
            
            original_name = attachment.get('name', 'attachment.jpg')
            normalized_name = normalize_filename(card_name, original_name, idx)
            output_path = output_dir / normalized_name
            
            if output_path.exists():
                downloaded_files.append(str(output_path))
                continue
            
            if download_attachment(url, output_path, trello_client):
                downloaded_files.append(str(output_path))
    
    logger.info(f"Downloaded {len(downloaded_files)}/{total_attachments} attachments")
    
    return downloaded_files

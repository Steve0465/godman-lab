from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TrelloError(Exception):
    pass


class TrelloClient:
    """Lightweight Trello API client with retry/backoff and minimal deps.

    Reads auth from environment variables TRELLO_KEY and TRELLO_TOKEN.
    Implements rate limit handling with exponential backoff (up to 5 retries).
    
    Parameters
    - api_key: Trello API key (optional, reads from TRELLO_KEY env var if not provided)
    - token: Trello API token (optional, reads from TRELLO_TOKEN env var if not provided)
    - base_url: Base API url (default https://api.trello.com/1)
    
    Raises
    - TrelloError: If credentials are missing or invalid
    """

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        token: Optional[str] = None, 
        base_url: str = "https://api.trello.com/1"
    ) -> None:
        # Read from env vars if not provided
        self.api_key = api_key or os.environ.get("TRELLO_KEY")
        self.token = token or os.environ.get("TRELLO_TOKEN")
        
        # Validate credentials
        if not self.api_key:
            raise TrelloError(
                "Missing TRELLO_KEY: set environment variable TRELLO_KEY or pass api_key parameter"
            )
        if not self.token:
            raise TrelloError(
                "Missing TRELLO_TOKEN: set environment variable TRELLO_TOKEN or pass token parameter"
            )
        
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "godman-lab-trello-audit/1.0",
        })
        
        print(f"✓ TrelloClient initialized (key: {self.api_key[:8]}...)")

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
    ) -> Any:
        """Perform a Trello API request with auth, 429 handling, and basic logging.

        Retries on 429 using Retry-After when present, otherwise exponential backoff.
        Raises TrelloError on non-success responses.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        merged_params = {"key": self.api_key, "token": self.token}
        if params:
            merged_params.update(params)

        attempt = 0
        backoff = 1.0
        while True:
            attempt += 1
            resp = self.session.request(method.upper(), url, params=merged_params, timeout=30)

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else backoff
                logger.warning("Trello rate limited (429). Sleeping %.2fs (attempt %d/%d)", sleep_s, attempt, max_retries)
                time.sleep(min(sleep_s, 60))
                backoff = min(backoff * 2, 60)
                if attempt <= max_retries:
                    continue

            if 200 <= resp.status_code < 300:
                try:
                    return resp.json()
                except ValueError:
                    return resp.text

            # For 5xx, allow retry with backoff
            if resp.status_code >= 500 and attempt <= max_retries:
                logger.warning("Trello server error %s. Retrying in %.1fs", resp.status_code, backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue

            # Non-retryable error
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            logger.error("Trello API error %s: %s", resp.status_code, detail)
            raise TrelloError(f"HTTP {resp.status_code}: {detail}")
    
    def get_board_cards(
        self, 
        board_id: str, 
        fields: str = "id,shortLink,name,idList,dateLastActivity"
    ) -> List[Dict[str, Any]]:
        """Fetch all cards for a board with specified fields.
        
        Args:
            board_id: Trello board ID
            fields: Comma-separated card field names to retrieve
            
        Returns:
            List of card dictionaries with requested fields
            
        Example:
            cards = client.get_board_cards("abc123", "id,name,desc,idList")
        """
        params = {"fields": fields}
        print(f"Fetching cards from board {board_id} (fields: {fields})")
        cards = self.request("GET", f"boards/{board_id}/cards", params=params)
        print(f"✓ Retrieved {len(cards)} cards")
        return cards if isinstance(cards, list) else []
    
    def get_board_lists(self, board_id: str) -> List[Dict[str, Any]]:
        """Fetch all lists for a board.
        
        Args:
            board_id: Trello board ID
            
        Returns:
            List of list dictionaries with id, name, closed, pos, etc.
            
        Example:
            lists = client.get_board_lists("abc123")
            bills_list = next(l for l in lists if l['name'] == 'BILLS')
        """
        print(f"Fetching lists from board {board_id}")
        lists = self.request("GET", f"boards/{board_id}/lists")
        print(f"✓ Retrieved {len(lists)} lists")
        return lists if isinstance(lists, list) else []
    
    def get_card(
        self,
        card_id_or_shortlink: str,
        *,
        attachments: bool = True,
        actions: bool = True,
        action_types: str = ""
    ) -> Dict[str, Any]:
        """Fetch a single card by ID or short link with full details.
        
        Args:
            card_id_or_shortlink: Full card ID or short link (e.g., "Z6JwfLEl")
            attachments: Include attachments (default: True)
            actions: Include actions/activity (default: True)
            action_types: Filter action types (e.g., "commentCard,updateCard:idList")
                         If empty, returns all action types
        
        Returns:
            Card dictionary with full details including attachments, actions, etc.
            
        Example:
            card = client.get_card("Z6JwfLEl", attachments=True, actions=True)
            card = client.get_card("abc123", action_types="commentCard,addAttachmentToCard")
        """
        params: Dict[str, Any] = {
            "attachments": str(attachments).lower(),
            "actions": "all" if actions else "none",
            "members": "true",
            "checklists": "all",
            "fields": "all",
        }
        
        if action_types:
            params["actions"] = action_types
        
        print(f"Fetching card {card_id_or_shortlink} (attachments={attachments}, actions={actions})")
        card = self.request("GET", f"cards/{card_id_or_shortlink}", params=params)
        
        if isinstance(card, dict):
            num_attachments = len(card.get("attachments", []))
            num_actions = len(card.get("actions", []))
            print(f"✓ Card: {card.get('name', 'Unknown')} ({num_attachments} attachments, {num_actions} actions)")
        
        return card if isinstance(card, dict) else {}
    
    def download_url(self, url: str, dest_path: Path) -> None:
        """Download a file from URL to destination path with streaming.
        
        Handles large files efficiently using streaming and shows progress.
        Creates parent directories if needed.
        
        Args:
            url: Full URL to download from (e.g., attachment URL)
            dest_path: Destination Path object where file will be saved
            
        Raises:
            TrelloError: If download fails
            
        Example:
            attachment_url = card['attachments'][0]['url']
            client.download_url(attachment_url, Path('/tmp/invoice.pdf'))
        """
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Downloading {url} -> {dest_path}")
        
        try:
            with self.session.get(url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                
                # Get file size if available
                total_size = int(resp.headers.get('content-length', 0))
                
                with open(dest_path, 'wb') as f:
                    downloaded = 0
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Simple progress indicator for large files
                            if total_size > 1_000_000:  # > 1MB
                                progress = (downloaded / total_size) * 100 if total_size else 0
                                print(f"  Progress: {progress:.1f}%", end='\r')
                
                if total_size > 1_000_000:
                    print()  # New line after progress
                    
                print(f"✓ Downloaded {downloaded:,} bytes to {dest_path}")
                
        except requests.RequestException as e:
            raise TrelloError(f"Failed to download {url}: {e}")

    def get_board_snapshot(self, board_id: str) -> Dict[str, Any]:
        """Fetch a rich board snapshot using the board endpoint with expansions.

        Attempts to include:
          - lists=all
          - cards=all with rich fields
          - members=all with selected fields
          - custom field items on cards when available
          - attachments and checklists
        """
        card_fields = ",".join([
            "id","name","desc","idList","closed","due","start","dateLastActivity",
            "labels","idMembers","checkItemStates","badges","shortUrl","url",
        ])
        member_fields = "fullName,username,avatarUrl"

        params = {
            "lists": "all",
            "cards": "all",
            "card_fields": card_fields,
            # Include checklists and attachments
            "checklists": "all",
            "card_attachments": "true",
            "attachments": "true",
            "attachment_fields": "all",
            # Members
            "members": "all",
            "member_fields": member_fields,
            # Include custom field items when Power-Up active
            "card_pluginData": "true",
            "customFieldItems": "true",
            # Board fields
            "fields": "name,desc,url,prefs,shortUrl,dateLastActivity,labelNames,closed"
        }
        data = self.request("GET", f"boards/{board_id}", params=params)

        # Some data requires additional calls on older boards; attempt to enrich minimally
        if isinstance(data, dict) and "customFields" not in data:
            try:
                custom_fields = self.request("GET", f"boards/{board_id}/customFields")
                if isinstance(custom_fields, list):
                    data["customFields"] = custom_fields
            except TrelloError:
                # Not critical
                pass

        return data

    def get_board_actions(
        self,
        board_id: str,
        since_iso: str,
        filters: str,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch board actions with pagination back to a since_iso cutoff.

        - Uses `before` param for pagination.
        - `filters` should include at least 'updateCard:idList' and 'createCard'.
        - Returns a list of action dicts sorted from newest to oldest as retrieved.
        """
        actions: List[Dict[str, Any]] = []
        before: Optional[str] = None
        cutoff = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))

        while True:
            params: Dict[str, Any] = {
                "limit": min(limit, 1000),
                "filter": filters,
                "since": since_iso,
            }
            if before:
                params["before"] = before

            batch = self.request("GET", f"boards/{board_id}/actions", params=params)
            if not batch:
                break

            # Append and decide whether to continue
            actions.extend(batch)

            # Determine if we've reached older than cutoff
            last_action = batch[-1]
            dt_str = last_action.get("date")
            if not dt_str:
                break
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            if dt <= cutoff:
                break

            before = last_action.get("id")  # Trello supports before=id for pagination

            # Safety stop
            if len(batch) < params["limit"]:
                break

        return actions

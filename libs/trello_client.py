from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TrelloError(Exception):
    pass


class TrelloClient:
    """Lightweight Trello API client with retry/backoff and minimal deps.

    Parameters
    - api_key: Trello API key
    - token: Trello API token
    - base_url: Base API url (default https://api.trello.com/1)
    """

    def __init__(self, api_key: str, token: str, base_url: str = "https://api.trello.com/1") -> None:
        self.api_key = api_key
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "godman-lab-trello-audit/1.0",
        })

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

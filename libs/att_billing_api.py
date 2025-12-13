"""
AT&T Billing API Client

Provides a clean Python interface to fetch AT&T billing data using authenticated
session cookies from the ATTClient scraper.

Uses requests.Session() with cookies from .cache/att_cookies.json
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

import requests


logger = logging.getLogger(__name__)


class ATTBillingAPI:
    """AT&T Billing API client using authenticated session cookies."""

    BASE_URL = "https://www.att.com/msapi/billorchestratorms"

    # Known endpoints from captured API traffic
    ENDPOINTS = {
        "current_balance": "/v2/currentbalance",
        "activity_history": "/v2/activityhistory",
        "bill_history": "/v2/billhistory/graphsummary",
        "bill_details": "/v2/billdetails",
        "notifications": "/v2/notifications/info",
        "bill_settings": "/v2/settings/getbillsettings",
        "highlights": "/v2/highlights/info",
        "promotions": "/v3/billOrchestrator/getactivepromotiondetails",
    }

    def __init__(self, cookie_file: Optional[Path] = None):
        """
        Initialize the AT&T Billing API client.

        Args:
            cookie_file: Path to cookie file. Defaults to .cache/att_cookies.json
        """
        self.cookie_file = cookie_file or Path(".cache/att_cookies.json")
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self) -> None:
        """Setup session with cookies and headers."""
        if not self.cookie_file.exists():
            raise FileNotFoundError(
                f"Cookie file not found: {self.cookie_file}\n"
                "Please run the ATTClient scraper or browser export first to authenticate."
            )

        try:
            with open(self.cookie_file, "r") as f:
                cookies = json.load(f)

            for cookie in cookies:
                self.session.cookies.set(
                    name=cookie["name"],
                    value=cookie["value"],
                    domain=cookie.get("domain", ".att.com"),
                    path=cookie.get("path", "/"),
                )

            logger.info(f"Loaded {len(cookies)} cookies from {self.cookie_file}")

        except Exception as e:
            raise RuntimeError(f"Failed to load cookies: {e}")

        # Headers aligned with real browser session hitting billing pages
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Origin": "https://www.att.com",
                "Referer": "https://www.att.com/acctmgmt/billing/mybillingcenter",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
        )

    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """
        Make authenticated API request.

        Args:
            endpoint: API endpoint path (e.g., "/v2/currentbalance")
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments to pass to requests

        Returns:
            Parsed JSON response

        Raises:
            requests.HTTPError: For HTTP errors (including 401/400)
            requests.RequestException: For network/connection errors
        """
        url = f"{self.BASE_URL}{endpoint}"
        logger.debug(f"{method} {url} kwargs={kwargs!r}")

        try:
            response = self.session.request(method, url, timeout=30, **kwargs)

            if response.status_code == 401:
                raise requests.HTTPError(
                    "Authentication failed (401). Session cookies may be expired.\n"
                    "Please refresh cookies from a logged-in browser session.",
                    response=response,
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response.text[:500]}")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    # ---- Public API methods ----

    def get_current_balance(self) -> Dict[str, Any]:
        """
        Get current account balance.

        Returns:
            Dictionary containing balance information.
        """
        logger.info("Fetching current balance")
        payload = {
            "accountNumber": "337058163",
            "accountType": "UVERSE",
            "billerId": "ENBLR",
            "systemId": "LS",
            "divisionId": "5T0",
            "accountStatus": "ACTIVE",
            "payAllFlag": False,
        }
        data = self._make_request(
            self.ENDPOINTS["current_balance"], method="POST", json=payload
        )
        logger.info(f"Current balance retrieved: {data}")
        return data

    def get_bill_history(self) -> Dict[str, Any]:
        """
        (Optional) Graph summary; not used for imports.

        NOTE: This endpoint is graph-only and may require a more complex payload.
        """
        logger.info("Fetching bill history graph summary")
        data = self._make_request(
            self.ENDPOINTS["bill_history"],
            method="POST",
            json={
                "account": "337058163",
                "accounttype": "ENBLR",
                "cvgWirelessBAN": "545134238301",
            },
        )
        return data

    def get_activity_history(self) -> Dict[str, Any]:
        """
        Fetch AT&T billing activity history.

        This is the REAL endpoint used by the importer to get bill entries.
        """
        logger.info("Fetching billing activity history")
        return self._make_request(
            self.ENDPOINTS["activity_history"],
            method="POST",
            json={
                "accountNumber": "337058163",
                "accountType": "ENBLR",
                "pageType": "bill",
                "systemId": "LS",
                "divisionId": "5T0",
                "cvgWirelessBAN": "545134238301",
            },
        )

    def get_bill_details(self, bill_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific bill.

        Args:
            bill_id: The bill identifier

        Returns:
            Dictionary containing detailed bill information.
        """
        logger.info(f"Fetching bill details for bill_id={bill_id!r}")
        data = self._make_request(
            self.ENDPOINTS["bill_details"],
            method="POST",
            json={
                "accountNumber": "337058163",
                "accountType": "ENBLR",
                "billId": bill_id,
            },
        )
        return data

    def download_bill_pdf(self, bill_id: str, out_dir: str = "data/att_bills") -> Path:
        """
        Download bill PDF to local directory.

        Args:
            bill_id: The bill identifier
            out_dir: Output directory for saved PDF (default: "data/att_bills")

        Returns:
            Path to the saved PDF file
        """
        logger.info(f"Downloading bill PDF for bill_id={bill_id!r}")

        bill_details = self.get_bill_details(bill_id)

        # Try to locate a PDF URL in the response
        pdf_fields = [
            "pdfUrl",
            "pdf_url",
            "downloadUrl",
            "download_url",
            "pdfDownloadUrl",
            "pdf_download_url",
            "billPdfUrl",
            "documentUrl",
            "document_url",
            "url",
            "link",
            "href",
        ]

        def find_pdf_url(data, depth: int = 0, max_depth: int = 10) -> Optional[str]:
            if depth > max_depth:
                return None

            if isinstance(data, dict):
                for field in pdf_fields:
                    if field in data:
                        value = data[field]
                        if isinstance(value, str) and ("pdf" in value.lower() or "bill" in value.lower()):
                            return value
                for value in data.values():
                    result = find_pdf_url(value, depth + 1, max_depth)
                    if result:
                        return result

            elif isinstance(data, list):
                for item in data:
                    result = find_pdf_url(item, depth + 1, max_depth)
                    if result:
                        return result

            return None

        pdf_url = find_pdf_url(bill_details)
        if not pdf_url:
            raise ValueError(
                f"No PDF URL found in bill details for bill_id={bill_id!r}. "
                f"Top-level keys: {list(bill_details.keys())}"
            )

        logger.info(f"Found PDF URL: {pdf_url}")

        # Normalize to absolute URL
        if pdf_url.startswith("/"):
            pdf_url = f"https://www.att.com{pdf_url}"
        elif not pdf_url.startswith("http"):
            pdf_url = f"https://www.att.com/{pdf_url}"

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"ATT_BILL_{bill_id}.pdf"

        resp = self.session.get(pdf_url, timeout=60, stream=True)
        resp.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"PDF saved: {file_path} ({file_path.stat().st_size:,} bytes)")
        return file_path

    def close(self) -> None:
        """Close the session."""
        self.session.close()
        logger.info("Session closed")

    def __enter__(self) -> "ATTBillingAPI":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

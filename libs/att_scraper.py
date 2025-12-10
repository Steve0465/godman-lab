import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from libs.credentials import get_att_credentials


logger = logging.getLogger(__name__)


class ATTClient:
    """AT&T web scraper client using Playwright."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the AT&T client.
        
        Args:
            headless: Run browser in headless mode
        """
        logger.info("Initializing AT&T client")
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.credentials = get_att_credentials()
        self.cookie_file = Path(".cache/att_cookies.json")
        self.cookie_file.parent.mkdir(exist_ok=True)
        
        self._launch_browser()
    
    def _launch_browser(self):
        """Launch Playwright browser."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self.page = self.context.new_page()
            logger.info("Browser launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
    
    def load_session(self) -> bool:
        """
        Load saved session cookies if available.
        
        Returns:
            True if cookies were loaded, False otherwise
        """
        if not self.cookie_file.exists():
            logger.info("No saved session found")
            return False
        
        try:
            with open(self.cookie_file, "r") as f:
                cookies = json.load(f)
            
            self.context.add_cookies(cookies)
            logger.info("Loaded saved session cookies")
            return True
        except Exception as e:
            logger.warning(f"Failed to load session cookies: {e}")
            return False
    
    def login(self, wait_for_mfa: bool = True):
        """
        Login to AT&T account.
        
        Args:
            wait_for_mfa: Wait for MFA completion if triggered
            
        Raises:
            Exception: If login fails
        """
        logger.info("Starting login process")
        
        try:
            # Navigate to login page
            self.page.goto("https://www.att.com/my/#/login", wait_until="networkidle")
            logger.info("Navigated to login page")
            
            # Wait for and fill username
            self.page.wait_for_selector("#userName", timeout=10000)
            self.page.fill("#userName", self.credentials["username"])
            logger.info("Entered username")
            
            # Click continue or submit
            self.page.click("button[type='submit']")
            
            # Wait for password field
            self.page.wait_for_selector("#password", timeout=10000)
            self.page.fill("#password", self.credentials["password"])
            logger.info("Entered password")
            
            # Submit login
            self.page.click("button[type='submit']")
            
            # Check for MFA
            try:
                mfa_detected = self.page.wait_for_selector(
                    "text=/verification|code|authenticate/i",
                    timeout=5000
                )
                if mfa_detected:
                    logger.warning("MFA detected - waiting for manual completion")
                    if wait_for_mfa:
                        # Wait for successful login (URL change or specific element)
                        self.page.wait_for_url("**/my/**", timeout=120000)
                        logger.info("MFA completed successfully")
            except PlaywrightTimeoutError:
                logger.info("No MFA detected or already completed")
            
            # Wait for post-login page load
            self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Save cookies
            self._save_cookies()
            logger.info("Login successful")
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    def _save_cookies(self):
        """Save session cookies to file."""
        try:
            cookies = self.context.cookies()
            with open(self.cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Saved session cookies to {self.cookie_file}")
        except Exception as e:
            logger.warning(f"Failed to save cookies: {e}")
    
    def _ensure_logged_in(self):
        """Ensure user is logged in, attempt login if not."""
        # Try loading saved session first
        if not self.load_session():
            logger.info("No saved session, performing fresh login")
            self.login()
        else:
            # Verify session is still valid
            try:
                self.page.goto("https://www.att.com/my/", timeout=10000)
                if "login" in self.page.url.lower():
                    logger.info("Session expired, performing fresh login")
                    self.login()
                else:
                    logger.info("Session is valid")
            except Exception as e:
                logger.warning(f"Session validation failed: {e}, performing fresh login")
                self.login()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get AT&T network status and outage information.
        
        Returns:
            Dictionary containing:
                - network_status: Overall network status
                - outages: List of active outages
                - repair_tickets: List of open repair tickets
                - case_numbers: List of case numbers
                - service_region: Service region details
                - timestamp: When data was collected
                
        Raises:
            Exception: If status retrieval fails
        """
        logger.info("Getting AT&T status")
        
        try:
            self._ensure_logged_in()
            
            # Navigate to outages page
            self.page.goto("https://www.att.com/outages/", wait_until="networkidle")
            logger.info("Navigated to outages page")
            
            # Wait for page to fully load
            self.page.wait_for_load_state("networkidle", timeout=15000)
            
            status_data = {
                "network_status": "unknown",
                "outages": [],
                "repair_tickets": [],
                "case_numbers": [],
                "service_region": None,
                "timestamp": None
            }
            
            # Scrape network status
            try:
                status_element = self.page.query_selector("[data-testid='network-status'], .network-status, text=/no outages|service normal/i")
                if status_element:
                    status_data["network_status"] = status_element.inner_text().strip()
                    logger.info(f"Network status: {status_data['network_status']}")
            except Exception as e:
                logger.warning(f"Could not find network status: {e}")
            
            # Scrape outages
            try:
                outage_elements = self.page.query_selector_all(".outage-item, [data-testid='outage'], .service-alert")
                for elem in outage_elements:
                    outage_text = elem.inner_text().strip()
                    if outage_text:
                        status_data["outages"].append(outage_text)
                logger.info(f"Found {len(status_data['outages'])} outages")
            except Exception as e:
                logger.warning(f"Could not scrape outages: {e}")
            
            # Scrape repair tickets
            try:
                ticket_elements = self.page.query_selector_all("[data-testid='repair-ticket'], .ticket-item, .repair-case")
                for elem in ticket_elements:
                    ticket_text = elem.inner_text().strip()
                    if ticket_text:
                        status_data["repair_tickets"].append(ticket_text)
                logger.info(f"Found {len(status_data['repair_tickets'])} repair tickets")
            except Exception as e:
                logger.warning(f"Could not scrape repair tickets: {e}")
            
            # Scrape case numbers
            try:
                case_pattern = r"(?:Case|Ticket|Reference)\s*#?\s*:?\s*([A-Z0-9\-]+)"
                page_content = self.page.content()
                import re
                matches = re.findall(case_pattern, page_content, re.IGNORECASE)
                status_data["case_numbers"] = list(set(matches))
                logger.info(f"Found {len(status_data['case_numbers'])} case numbers")
            except Exception as e:
                logger.warning(f"Could not extract case numbers: {e}")
            
            # Scrape service region
            try:
                region_element = self.page.query_selector("[data-testid='service-region'], .service-address, .account-address")
                if region_element:
                    status_data["service_region"] = region_element.inner_text().strip()
                    logger.info(f"Service region: {status_data['service_region']}")
            except Exception as e:
                logger.warning(f"Could not find service region: {e}")
            
            # Add timestamp
            from datetime import datetime
            status_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            logger.info("Successfully retrieved status data")
            return status_data
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise
    
    def close(self):
        """Shutdown browser and cleanup resources."""
        logger.info("Closing AT&T client")
        
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

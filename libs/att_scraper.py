import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, Optional, Any, List
from functools import wraps

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from libs.credentials import get_att_credentials


logger = logging.getLogger(__name__)


def retry_on_failure(max_attempts=3, backoff_base=2.0):
    """Decorator to retry function calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = backoff_base ** attempt + random.uniform(0, 1)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator


class ATTClient:
    """AT&T web scraper client using Playwright."""
    
    def __init__(self, headless: bool = True, enable_har: bool = False):
        """
        Initialize the AT&T client.
        
        Args:
            headless: Run browser in headless mode
            enable_har: Enable network traffic recording (HAR)
        """
        logger.info("Initializing AT&T client")
        self.headless = headless
        self.enable_har = enable_har
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.credentials = get_att_credentials()
        self.cookie_file = Path(".cache/att_cookies.json")
        self.har_file = Path(".cache/att_network.har")
        self.api_urls_file = Path(".cache/att_api_urls.json")
        self.cookie_file.parent.mkdir(exist_ok=True)
        self.captured_api_urls: List[str] = []
        
        self._launch_browser()
    
    def _launch_browser(self):
        """Launch Playwright browser with stealth configuration."""
        try:
            self.playwright = sync_playwright().start()
            
            # Launch with stealth settings
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            # Randomize viewport for stealth
            viewport_width = random.randint(1280, 1920)
            viewport_height = random.randint(720, 1080)
            
            # Context with stealth settings and optional HAR recording
            context_options = {
                "viewport": {"width": viewport_width, "height": viewport_height},
                "user_agent": self._get_random_user_agent(),
                "locale": "en-US",
                "timezone_id": "America/New_York",
                "color_scheme": "light",
                "extra_http_headers": {
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            }
            
            # Enable HAR recording if requested
            if self.enable_har:
                context_options["record_har_path"] = str(self.har_file)
                logger.info(f"HAR recording enabled: {self.har_file}")
            
            self.context = self.browser.new_context(**context_options)
            
            # Add stealth scripts
            self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """)
            
            self.page = self.context.new_page()
            
            # Setup network request interceptor for API discovery
            self._setup_network_interceptor()
            
            logger.info(f"Browser launched successfully (viewport: {viewport_width}x{viewport_height})")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
    
    def _get_random_user_agent(self) -> str:
        """Get a randomized realistic user agent."""
        agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        return random.choice(agents)
    
    def _setup_network_interceptor(self):
        """Setup network request interceptor to capture API URLs."""
        def log_request(route, request):
            url = request.url
            method = request.method
            
            # Capture API endpoints
            if any(keyword in url.lower() for keyword in ['api', 'graphql', 'account', 'service', 'status', 'outage']):
                if url not in self.captured_api_urls:
                    self.captured_api_urls.append(url)
                    logger.debug(f"Captured API URL: {method} {url}")
            
            route.continue_()
        
        self.page.route("**/*", log_request)
    
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
    
    def validate_session(self) -> bool:
        """
        Validate if current session is still active.
        
        Returns:
            True if session is valid, False otherwise
        """
        try:
            logger.info("Validating session...")
            
            # Try to access account page
            response = self.page.goto("https://www.att.com/my/", wait_until="domcontentloaded", timeout=15000)
            
            if not response:
                logger.warning("No response from session validation")
                return False
            
            # Wait a bit for redirects
            time.sleep(2)
            
            current_url = self.page.url
            page_content = self.page.content().lower()
            
            # Check if we're on a login page
            if "signin.att.com" in current_url or "login" in current_url:
                logger.info("Session expired - redirected to login page")
                return False
            
            # Check for login form elements
            if "user id" in page_content and "continue" in page_content:
                logger.info("Session expired - login form detected")
                return False
            
            # Check for authenticated content
            if any(keyword in page_content for keyword in ["my account", "account overview", "billing"]):
                logger.info("Session is valid - authenticated content detected")
                return True
            
            logger.warning("Session validation inconclusive")
            return False
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
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
            
            # Wait for and fill username (User ID field) with realistic typing
            self.page.wait_for_selector("#userID", timeout=15000)
            self._human_type("#userID", self.credentials["username"])
            logger.info("Entered username")
            
            # Small delay before clicking
            time.sleep(random.uniform(0.5, 1.5))
            
            # Click Continue button (first step)
            self.page.click("button:has-text('Continue')")
            logger.info("Clicked Continue button")
            
            # Wait for password field to appear (second step)
            self.page.wait_for_selector("#password", timeout=15000)
            self._human_type("#password", self.credentials["password"])
            logger.info("Entered password")
            
            # Small delay before clicking
            time.sleep(random.uniform(0.5, 1.5))
            
            # Submit login (Sign in button)
            self.page.click("button:has-text('Sign in')")
            
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
    
    def _human_type(self, selector: str, text: str):
        """Type text with human-like delays."""
        self.page.fill(selector, "")  # Clear first
        for char in text:
            self.page.type(selector, char, delay=random.uniform(50, 150))
    
    def _save_cookies(self):
        """Save session cookies to file."""
        try:
            cookies = self.context.cookies()
            with open(self.cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Saved session cookies to {self.cookie_file}")
        except Exception as e:
            logger.warning(f"Failed to save cookies: {e}")
    
    def _save_api_urls(self):
        """Save captured API URLs to file."""
        try:
            if self.captured_api_urls:
                with open(self.api_urls_file, "w") as f:
                    json.dump({
                        "urls": self.captured_api_urls,
                        "timestamp": time.time()
                    }, f, indent=2)
                logger.info(f"Saved {len(self.captured_api_urls)} API URLs to {self.api_urls_file}")
        except Exception as e:
            logger.warning(f"Failed to save API URLs: {e}")
    
    @retry_on_failure(max_attempts=2, backoff_base=1.5)
    def _ensure_logged_in(self):
        """Ensure user is logged in with session validation and auto re-login."""
        # Try loading saved session first
        session_loaded = self.load_session()
        
        if not session_loaded:
            logger.info("No saved session, performing fresh login")
            self.login()
            return
        
        # Validate the loaded session
        if self.validate_session():
            logger.info("Session validated successfully")
            return
        
        # Session invalid, clear cookies and re-login
        logger.info("Session invalid, clearing cookies and re-authenticating")
        try:
            self.context.clear_cookies()
            if self.cookie_file.exists():
                self.cookie_file.unlink()
        except Exception as e:
            logger.warning(f"Error clearing cookies: {e}")
        
        self.login()
    
    @retry_on_failure(max_attempts=2, backoff_base=2.0)
    def get_account_dashboard(self) -> Dict[str, Any]:
        """
        Get AT&T account dashboard information.
        
        Returns:
            Dictionary containing account overview, services, and status
            
        Raises:
            Exception: If dashboard retrieval fails
        """
        logger.info("Getting AT&T account dashboard")
        
        try:
            self._ensure_logged_in()
            
            # Navigate to account overview/dashboard
            logger.info("Navigating to account dashboard")
            self.page.goto("https://www.att.com/my/", wait_until="domcontentloaded", timeout=60000)
            
            # Wait for dynamic content
            time.sleep(3)
            
            # Try to find and click account or services link
            try:
                account_link = self.page.query_selector("a[href*='account'], a[href*='overview'], a:has-text('Account')")
                if account_link:
                    logger.info("Clicking account overview link")
                    account_link.click()
                    self.page.wait_for_load_state("domcontentloaded", timeout=30000)
                    time.sleep(2)
            except Exception as e:
                logger.debug(f"Could not click account link: {e}")
            
            dashboard_data = {
                "account_status": "unknown",
                "services": [],
                "alerts": [],
                "current_url": self.page.url,
                "timestamp": None
            }
            
            # Get page content
            try:
                page_text = self.page.inner_text("body")
                dashboard_data["page_preview"] = page_text[:1000]
                logger.debug(f"Dashboard preview: {page_text[:300]}")
            except Exception as e:
                logger.warning(f"Could not get page text: {e}")
            
            # Look for service status indicators
            try:
                if "no issues" in self.page.content().lower() or "service is working" in self.page.content().lower():
                    dashboard_data["account_status"] = "All services operational"
                elif "issue" in self.page.content().lower() or "problem" in self.page.content().lower():
                    dashboard_data["account_status"] = "Service issues detected"
            except Exception as e:
                logger.warning(f"Could not determine account status: {e}")
            
            # Try to extract service information
            try:
                service_elements = self.page.query_selector_all("[class*='service'], [class*='product'], [data-testid*='service']")
                for elem in service_elements[:10]:
                    text = elem.inner_text().strip()
                    if text and len(text) > 10:
                        dashboard_data["services"].append(text)
                logger.info(f"Found {len(dashboard_data['services'])} services")
            except Exception as e:
                logger.warning(f"Could not extract services: {e}")
            
            # Look for alerts or notifications
            try:
                alert_elements = self.page.query_selector_all("[class*='alert'], [class*='notification'], [role='alert']")
                for elem in alert_elements[:5]:
                    text = elem.inner_text().strip()
                    if text:
                        dashboard_data["alerts"].append(text)
                logger.info(f"Found {len(dashboard_data['alerts'])} alerts")
            except Exception as e:
                logger.warning(f"Could not extract alerts: {e}")
            
            # Add timestamp
            from datetime import datetime
            dashboard_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            # Save captured API URLs
            self._save_api_urls()
            
            logger.info("Successfully retrieved account dashboard")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get account dashboard: {e}")
            raise
    
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
            
            # Navigate to outages page (use domcontentloaded instead of networkidle)
            self.page.goto("https://www.att.com/outages/", wait_until="domcontentloaded", timeout=60000)
            logger.info("Navigated to outages page")
            
            # Wait for page to be interactive
            self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            logger.info("Page DOM loaded")
            
            # Click "Sign in" button to see account-specific outages
            try:
                sign_in_button = self.page.query_selector("a:has-text('Sign in'), button:has-text('Sign in')")
                if sign_in_button:
                    logger.info("Clicking Sign in button to view account outages")
                    sign_in_button.click()
                    self.page.wait_for_load_state("domcontentloaded", timeout=30000)
                    logger.info("Signed in to view account outages")
            except Exception as e:
                logger.warning(f"Could not click sign in button (may already be authenticated): {e}")
            
            # Wait a bit for dynamic content to load
            import time
            time.sleep(2)
            
            status_data = {
                "network_status": "unknown",
                "outages": [],
                "repair_tickets": [],
                "case_numbers": [],
                "service_region": None,
                "timestamp": None,
                "raw_content": None
            }
            
            # Get all text content for analysis
            try:
                page_text = self.page.inner_text("body")
                status_data["raw_content"] = page_text[:500]  # First 500 chars for debugging
                logger.info(f"Page content preview: {page_text[:200]}")
            except Exception as e:
                logger.warning(f"Could not get page text: {e}")
            
            # Scrape network status
            try:
                # Look for status indicators
                if "no outages" in self.page.content().lower():
                    status_data["network_status"] = "No outages detected"
                elif "outage" in self.page.content().lower():
                    status_data["network_status"] = "Possible outage detected"
                    
                logger.info(f"Network status: {status_data['network_status']}")
            except Exception as e:
                logger.warning(f"Could not determine network status: {e}")
            
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
            
            # Scrape case numbers (look for actual case number patterns)
            try:
                case_pattern = r"(?:Case|Ticket|Reference|Repair)\s*#?\s*:?\s*([A-Z]{2,}\d{6,}|\d{10,})"
                page_content = self.page.content()
                import re
                matches = re.findall(case_pattern, page_content, re.IGNORECASE)
                status_data["case_numbers"] = list(set(matches)) if matches else []
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
            # Save API URLs before closing
            self._save_api_urls()
            
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

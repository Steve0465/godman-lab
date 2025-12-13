# AT&T Billing API Status

## Current Status: ⚠️ Partially Working

The AT&T billing API client (`libs/att_billing_api.py`) is **set up and functional** but requires additional work to match AT&T's specific API requirements.

## What Works ✓

- ✅ **Cookie Loading**: Successfully loads Playwright cookies from `.cache/att_cookies.json`
- ✅ **Session Management**: Maintains authenticated session with proper headers
- ✅ **Request Infrastructure**: HTTP client properly configured with timeouts and error handling
- ✅ **Syntax Fixed**: All Python syntax errors resolved

## Current Issues ⚠️

### 1. HTTP Method Mismatch (405 Errors)
- AT&T endpoints return `405 Method Not Allowed` for GET requests
- **Likely cause**: These endpoints require POST requests

### 2. Missing Request Payloads (400 Errors)
- POST requests return `400 Bad Request`
- **Likely cause**: Missing required JSON payload or headers

### 3. API Discovery Incomplete
The captured API URLs show these endpoints exist:
```
/v2/currentbalance
/v2/activityhistory
/v2/billhistory/graphsummary
/v2/billdetails
/v2/notifications/info
/v2/settings/getbillsettings
```

## Next Steps to Get Fully Working

### Option 1: Capture Full HTTP Requests (Recommended)
Use the AT&T scraper with HAR recording to capture complete request details:
```python
from libs.att_scraper import ATTClient

# Enable HAR recording to capture full requests
client = ATTClient(headless=False, enable_har=True)
client.login()

# Navigate to billing pages to trigger API calls
client.page.goto("https://www.att.com/acctmgmt/billing/mybillingcenter")
client.page.wait_for_timeout(5000)  # Let APIs load

client.close()
# Check .cache/att_network.har for full request details
```

Then inspect `.cache/att_network.har` to find:
- Exact HTTP methods (POST vs GET)
- Required request payloads
- Required headers (beyond what we have)
- Response structures

### Option 2: Browser DevTools Inspection
1. Login to AT&T website in browser
2. Open DevTools → Network tab
3. Navigate to billing pages
4. Find API calls to `billorchestratorms`
5. Copy as cURL or inspect request details
6. Update `att_billing_api.py` with correct:
   - Request methods
   - JSON payloads
   - Additional headers

### Option 3: Use Scraper Instead of API
For immediate functionality, use the existing `ATTClient` scraper which already works:
```python
from libs.att_scraper import ATTClient

client = ATTClient(headless=False)
client.login()

# Navigate and extract data from pages
client.page.goto("https://www.att.com/acctmgmt/billing/mybillingcenter")
# Use page.locator() to extract bill amounts, dates, etc.

client.close()
```

## Example: What a Working Request Might Look Like

Based on typical AT&T API patterns, requests probably need:
```python
# Example POST request with account context
result = session.post(
    "https://www.att.com/msapi/billorchestratorms/v2/currentbalance",
    json={
        "accountNumber": "337058163",  # From captured URLs
        "accountType": "UVERSE",
        # Other required fields...
    },
    headers={
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        # Possibly CSRF tokens or other security headers
    }
)
```

## Recommendation

**Short term (today)**: Use the Playwright scraper (`ATTClient`) which already works for automation.

**Long term (next sprint)**: Capture HAR file or inspect browser requests to get exact API specifications, then update `att_billing_api.py` with correct request formats.

## Files to Check

- `libs/att_billing_api.py` - The API client (needs request format updates)
- `libs/att_scraper.py` - Working Playwright scraper (use this now)
- `.cache/att_cookies.json` - Valid authentication cookies (working ✓)
- `.cache/att_network.har` - Network capture (create with enable_har=True)
- `.cache/att_api_urls.json` - List of discovered endpoints (exists ✓)

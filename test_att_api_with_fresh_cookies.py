#!/usr/bin/env python3
"""Update AT&T cookies and test API"""

import json
from pathlib import Path

PAYLOAD_FILE = Path("fresh_cookies_payload.json")


def load_cookie_payload() -> list[dict]:
    if not PAYLOAD_FILE.exists():
        raise SystemExit(f"Missing {PAYLOAD_FILE}. Drop the latest cookie export there and retry.")

    try:
        return json.loads(PAYLOAD_FILE.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guardrail
        raise SystemExit(f"Invalid JSON in {PAYLOAD_FILE}: {exc}") from exc


fresh_cookies_data = load_cookie_payload()

# Some cookies occasionally pick up smart characters copied from browsers.
# Normalize them back to plain ASCII so requests can build headers safely.
UNICODE_FIXES = {
    "С": "C",  # Cyrillic capital letter Es
    "Т": "T",  # Cyrillic capital letter Te
}


def sanitize_cookie_value(value: str) -> str:
    normalized = "".join(UNICODE_FIXES.get(ch, ch) for ch in value)
    try:
        normalized.encode("latin-1")
        return normalized
    except UnicodeEncodeError:
        # Fallback: replace high Unicode with \uXXXX escapes to keep headers ASCII-safe.
        return normalized.encode("unicode_escape").decode("ascii")


for cookie in fresh_cookies_data:
    cookie_value = cookie.get("value", "")
    cookie_name = cookie.get("name", "")
    cookie["value"] = sanitize_cookie_value(cookie_value)
    cookie["name"] = sanitize_cookie_value(cookie_name)

# Save cookies
cookie_file = Path(".cache/att_cookies.json")
cookie_file.parent.mkdir(exist_ok=True)

with open(cookie_file, "w") as f:
    json.dump(fresh_cookies_data, f, indent=2)

print(f"✓ Saved {len(fresh_cookies_data)} cookies to {cookie_file}")
print(f"✓ File size: {cookie_file.stat().st_size:,} bytes\n")

# Test the API
print("Testing AT&T Billing API...")
print("=" * 70)

from libs.att_billing_api import ATTBillingAPI


def format_http_error(err: Exception) -> str:
    response = getattr(err, "response", None)
    if response is None:
        return str(err)

    body_snippet = response.text[:500] if response.text else "<empty body>"
    return f"{err}\nResponse body snippet:\n{body_snippet}"

try:
    with ATTBillingAPI() as api:
        # Test 1: Current balance
        print("\n1. Current Balance:")
        try:
            balance = api.get_current_balance()
            print("✅ SUCCESS!")
            print(json.dumps(balance, indent=2))
        except Exception as e:
            print(f"❌ FAILED: {format_http_error(e)}")
        
        # Test 2: Activity history  
        print("\n2. Activity History:")
        try:
            activity = api.get_activity_history()
            print("✅ SUCCESS!")
            items = activity.get("items", []) or activity.get("activityList", [])
            print(f"Found {len(items)} activity items")
            if items:
                print("\nFirst item:")
                print(json.dumps(items[0], indent=2))
        except Exception as e:
            print(f"❌ FAILED: {format_http_error(e)}")
        
        # Test 3: Bill history
        print("\n3. Bill History:")
        try:
            bills = api.get_bill_history()
            print("✅ SUCCESS!")
            print(json.dumps(bills, indent=2))
        except Exception as e:
            print(f"❌ FAILED: {format_http_error(e)}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("Testing complete!")

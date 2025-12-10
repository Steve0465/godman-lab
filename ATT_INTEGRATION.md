# AT&T Integration

Automated AT&T account monitoring and status checking using web scraping.

## Features

- **Credential Management**: Secure credential storage via macOS Keychain or environment variables
- **Session Persistence**: Cookie-based session management to minimize logins
- **MFA Support**: Handles multi-factor authentication when triggered
- **Status Monitoring**: Scrapes network status, outages, repair tickets, and service information
- **CLI Tool**: Easy-to-use command-line interface
- **AI Integration**: Tool available for AI agents to query AT&T status

## Installation

1. Install Playwright and browser:
```bash
pip install playwright
playwright install chromium
```

2. Set up credentials (choose one method):

### Option A: Environment Variables
Create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your credentials
```

### Option B: macOS Keychain
```bash
# Add username
security add-generic-password -s "att-login" -a "username" -w "your_username"

# Add password
security add-generic-password -s "att-login" -a "password" -w "your_password"
```

## Usage

### CLI Command

Get AT&T status:
```bash
python -m cli.godman.main att status
```

This will output JSON with:
- Network status
- Active outages
- Open repair tickets
- Case numbers
- Service region
- Timestamp

### Python API

```python
from libs.att_scraper import ATTClient

# Use context manager for automatic cleanup
with ATTClient() as client:
    status = client.get_status()
    print(status)
```

### AI Tool Integration

The AT&T status tool is registered in `.codex/tools.json` and can be used by AI agents:

```python
from godman_ai.tools.att_status_tool import run_att_status

# Query specific information
result = run_att_status("outages")
result = run_att_status("repair tickets")
result = run_att_status("network status")
result = run_att_status("all")
```

## Architecture

### Components

1. **libs/credentials.py**
   - Secure credential retrieval
   - Supports macOS Keychain and environment variables
   - Automatic .env file loading

2. **libs/att_scraper.py**
   - `ATTClient` class using Playwright
   - Automated login with MFA handling
   - Session cookie persistence
   - Status page scraping

3. **cli/godman/att.py**
   - Typer-based CLI interface
   - JSON output formatting
   - Error handling

4. **godman_ai/tools/att_status_tool.py**
   - AI tool wrapper
   - Intent-based filtering
   - Multiple output formatters

### Data Flow

```
User Request
    ↓
CLI/Tool → ATTClient → Playwright → AT&T Website
    ↑                                      ↓
    └────────── Parsed Data ───────────────┘
```

## Configuration

### Cookie Cache

Session cookies are stored in `.cache/att_cookies.json` to minimize logins. Delete this file to force a fresh login:
```bash
rm .cache/att_cookies.json
```

### Headless Mode

By default, the browser runs in headless mode. To see the browser (useful for debugging MFA):
```python
client = ATTClient(headless=False)
```

## Error Handling

The scraper includes robust error handling:
- Credential validation
- Login failure detection
- MFA timeout handling
- Network error recovery
- Graceful browser cleanup

## Security Notes

- Never commit `.env` file or credentials to version control
- Keychain is the most secure option on macOS
- Session cookies contain authentication tokens - protect `.cache/` directory
- Consider rotating credentials regularly

## Troubleshooting

### "Credentials not found" error
Ensure you've set credentials via environment variables or Keychain.

### MFA issues
If MFA times out, run with `headless=False` to manually complete verification:
```python
client = ATTClient(headless=False)
client.login(wait_for_mfa=True)
```

### Stale session
Delete the cookie cache:
```bash
rm .cache/att_cookies.json
```

### Playwright not installed
```bash
pip install playwright
playwright install chromium
```

## Future Enhancements

- [ ] Support for billing information scraping
- [ ] Account usage statistics
- [ ] Automated alert notifications
- [ ] Multiple account support
- [ ] Historical status tracking
- [ ] Web dashboard integration

## Contributing

When adding new scrapers or features:
1. Update selectors in `libs/att_scraper.py`
2. Add formatters in `godman_ai/tools/att_status_tool.py`
3. Update this README
4. Test with real AT&T account

## License

Internal use only - Part of Godman Lab automation suite.

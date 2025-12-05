# GodmanAI API Security

## Overview

The GodmanAI API server includes token-based authentication to secure mutating endpoints.

## Setting Up Authentication

### 1. Generate an API Token

Create a secure random token:

```bash
# macOS/Linux
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Configure the Token

Set the `GODMAN_API_TOKEN` environment variable:

```bash
# Add to ~/.zshrc or ~/.bashrc
export GODMAN_API_TOKEN="your-secure-token-here"

# Or add to .env file in repo root
echo "GODMAN_API_TOKEN=your-secure-token-here" >> .env
```

Reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### 3. Start the Server

```bash
godman server
```

The server will:
- Log a warning if no token is configured
- Require `Authorization: Bearer <token>` header for mutating endpoints
- Allow read-only endpoints without authentication

## Protected Endpoints

The following endpoints require authentication:

- `POST /run` - Run orchestrator
- `POST /agent` - Run agent loop  
- `POST /queue/enqueue` - Add job to queue
- `POST /memory/add` - Add to memory

## Making Authenticated Requests

### Using curl

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"input": "scan receipt.pdf"}'
```

### Using Python

```python
import requests

headers = {
    "Authorization": "Bearer your-token-here",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://127.0.0.1:8000/run",
    headers=headers,
    json={"input": "scan receipt.pdf"}
)

print(response.json())
```

## Exposing Server Publicly

### Using Cloudflare Tunnel

1. **Install cloudflared:**

```bash
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

2. **Start the API server:**

```bash
godman server
```

3. **In another terminal, start the tunnel:**

```bash
godman tunnel
```

This will output a public URL like:
```
https://random-name.trycloudflare.com
```

4. **Access your API remotely:**

```bash
curl -X POST https://random-name.trycloudflare.com/run \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"input": "process data"}'
```

### Custom Tunnel URL

```bash
# Tunnel to a different local port
godman tunnel --url http://127.0.0.1:8080
```

## Security Best Practices

1. **Never commit tokens** - Add `.env` to `.gitignore`
2. **Use strong tokens** - Minimum 32 characters, random hex
3. **Rotate tokens** - Change periodically and after suspected exposure
4. **Use HTTPS** - Always tunnel through cloudflared or reverse proxy
5. **Limit access** - Only expose publicly when necessary
6. **Monitor logs** - Check `.godman/logs/` for suspicious activity

## Troubleshooting

### Token not recognized

```bash
# Verify token is set
echo $GODMAN_API_TOKEN

# Restart server after setting token
godman server
```

### 401 Unauthorized

- Check Authorization header format: `Bearer <token>`
- Ensure token matches server configuration
- Verify no extra spaces or special characters

### cloudflared not found

```bash
# Check installation
which cloudflared

# Install if missing
brew install cloudflare/cloudflare/cloudflared
```

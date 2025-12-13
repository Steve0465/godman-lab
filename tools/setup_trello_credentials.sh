#!/bin/bash
# Trello Credentials Setup Script

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          TRELLO API CREDENTIALS SETUP                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if credentials already exist
if [ -n "$TRELLO_API_KEY" ] && [ -n "$TRELLO_TOKEN" ]; then
    echo "⚠️  Credentials are already set in this session!"
    echo ""
    echo "Current API Key: ${TRELLO_API_KEY:0:8}..."
    echo "Current Token: ${TRELLO_TOKEN:0:8}..."
    echo ""
    read -p "Do you want to replace them? (y/n): " replace
    if [ "$replace" != "y" ]; then
        echo "Keeping existing credentials. Exiting."
        exit 0
    fi
fi

echo "📝 STEP 1: Get Your Trello API Key"
echo "──────────────────────────────────────────────────────────────"
echo "1. Open this URL in your browser:"
echo "   https://trello.com/power-ups/admin"
echo ""
echo "2. Log in to Trello if needed"
echo "3. Click 'New' or find your existing API key"
echo "4. Copy the API Key (looks like: a1b2c3d4e5f6...)"
echo ""
read -p "Paste your API KEY here: " api_key

if [ -z "$api_key" ]; then
    echo "❌ Error: API Key cannot be empty"
    exit 1
fi

echo ""
echo "📝 STEP 2: Get Your Trello Token"
echo "──────────────────────────────────────────────────────────────"
echo "1. On the same page, look for the 'Token' link"
echo "2. Click 'Token' (or manually visit the authorize URL)"
echo "3. Click 'Allow' to authorize"
echo "4. Copy the Token (looks like: abc123def456...)"
echo ""
read -p "Paste your TOKEN here: " token

if [ -z "$token" ]; then
    echo "❌ Error: Token cannot be empty"
    exit 1
fi

echo ""
echo "✅ Credentials received!"
echo ""

# Set for current session
export TRELLO_API_KEY="$api_key"
export TRELLO_TOKEN="$token"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          CREDENTIALS CONFIGURED                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Credentials are now set for this terminal session"
echo ""
echo "API Key: ${api_key:0:8}..."
echo "Token:   ${token:0:8}..."
echo ""

# Save to .env file (optional)
read -p "📁 Save credentials to .env file? (y/n): " save_env
if [ "$save_env" = "y" ]; then
    echo "# Trello API Credentials" > .env
    echo "# Generated on $(date)" >> .env
    echo "export TRELLO_API_KEY=\"$api_key\"" >> .env
    echo "export TRELLO_TOKEN=\"$token\"" >> .env
    
    echo "✅ Saved to .env file"
    echo ""
    echo "To use in future sessions, run:"
    echo "  source .env"
    echo ""
    
    # Add .env to .gitignore if not already there
    if [ -f .gitignore ]; then
        if ! grep -q "^\.env$" .gitignore; then
            echo ".env" >> .gitignore
            echo "✅ Added .env to .gitignore"
        fi
    else
        echo ".env" > .gitignore
        echo "✅ Created .gitignore with .env"
    fi
fi

echo ""
echo "🚀 READY TO EXPORT!"
echo "──────────────────────────────────────────────────────────────"
echo "Run this command to export your board:"
echo ""
echo "  python tools/trello_export.py --board \"Memphis Pool\" --verbose"
echo ""
echo "Or test with:"
echo ""
echo "  python tools/trello_export.py --help"
echo ""


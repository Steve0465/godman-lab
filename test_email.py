#!/usr/bin/env python3
"""Test email configuration."""

import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Testing Email Configuration")
print("=" * 60)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECIPIENT = os.getenv("RECIPIENT")

print(f"Server: {SMTP_SERVER}")
print(f"Port: {SMTP_PORT}")
print(f"From: {EMAIL_USER}")
print(f"To: {RECIPIENT}")
print()

if not EMAIL_USER or not EMAIL_PASS:
    print("❌ Email credentials not configured")
    exit(1)

print("Attempting to connect to SMTP server...")

try:
    # Create test email
    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = RECIPIENT
    msg["Subject"] = "🧾 Receipt System Test - Setup Complete!"
    
    msg.set_content("""
This is a test email from your receipt processing system.

✅ Email automation is working!

Your system is now configured to:
- Process receipts with OCR + AI
- Send monthly expense summaries automatically

Next steps:
1. Drop receipts in the scans/ folder
2. Run: python process_receipts.py
3. Get monthly summaries via email

--
Sent from godman-lab receipt processor
    """)
    
    # Send via SMTP
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
        server.set_debuglevel(0)
        server.starttls()
        print("✓ TLS connection established")
        
        server.login(EMAIL_USER, EMAIL_PASS)
        print("✓ Authentication successful")
        
        server.send_message(msg)
        print("✓ Email sent successfully")
    
    print()
    print("=" * 60)
    print("✅ EMAIL SYSTEM IS WORKING!")
    print("=" * 60)
    print()
    print(f"Check your inbox: {RECIPIENT}")
    print("You should receive a test email shortly.")
    
except smtplib.SMTPAuthenticationError as e:
    print()
    print("❌ Authentication Failed")
    print()
    print("This usually means:")
    print("1. Password is incorrect")
    print("2. App password is required (not regular password)")
    print("3. 2-Factor Authentication needs to be enabled")
    print()
    print("To fix:")
    print("1. Enable 2FA: https://account.microsoft.com/security")
    print("2. Create app password: https://account.live.com/proofs/AppPassword")
    print("3. Update .env with the app password")
    print()
    print(f"Error details: {e}")
    exit(1)
    
except Exception as e:
    print()
    print(f"❌ Connection Error: {e}")
    print()
    print("Troubleshooting:")
    print("- Check your internet connection")
    print("- Verify SMTP server: smtp.office365.com")
    print("- Try again in a few minutes")
    exit(1)

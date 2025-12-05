"""
Email Monitor Tool - Auto-extract invoices, bills, and important emails
"""
from ..engine import BaseTool
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailMonitorTool(BaseTool):
    """Monitor email inbox and auto-process messages"""
    
    name = "email_monitor"
    description = "Monitors email for invoices, bills, and important messages"
    
    def run(self, email: str = None, password: str = None, **kwargs):
        """
        Monitor email inbox
        
        Args:
            email: Email address (or load from settings)
            password: App password (or load from settings)
        """
        try:
            import imaplib
            import email as email_lib
            from email.header import decode_header
        except ImportError:
            return {"error": "imaplib not available"}
        
        # Load from environment if not provided
        email = email or os.getenv("EMAIL_USER")
        password = password or os.getenv("EMAIL_PASSWORD")
        
        if not email or not password:
            return {"error": "Email credentials not provided"}
        
        # Determine IMAP server
        if "gmail" in email:
            imap_server = "imap.gmail.com"
        elif "outlook" in email or "hotmail" in email:
            imap_server = "imap-mail.outlook.com"
        else:
            return {"error": "Unsupported email provider"}
        
        try:
            # Connect to email
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email, password)
            mail.select("inbox")
            
            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")
            email_ids = messages[0].split()
            
            results = []
            for email_id in email_ids[:10]:  # Process last 10 unread
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email_lib.message_from_bytes(msg_data[0][1])
                
                # Decode subject
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                from_addr = msg.get("From")
                
                # Check if it's a bill/invoice
                keywords = ["invoice", "bill", "payment", "receipt", "statement"]
                is_financial = any(kw in subject.lower() for kw in keywords)
                
                results.append({
                    "from": from_addr,
                    "subject": subject,
                    "is_financial": is_financial,
                    "email_id": email_id.decode()
                })
            
            mail.close()
            mail.logout()
            
            return {
                "status": "success",
                "unread_count": len(email_ids),
                "processed": len(results),
                "emails": results
            }
            
        except Exception as e:
            return {"error": str(e)}

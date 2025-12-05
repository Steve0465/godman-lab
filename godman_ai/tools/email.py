"""Email Tool - Send and read emails."""

from typing import Any, Dict, List
import os


class EmailTool:
    """Send and read emails using SMTP/IMAP."""
    
    name = "email"
    description = "Send and read emails"
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Perform email operations.
        
        Args:
            action: 'send' or 'read'
            **kwargs: Action-specific parameters
            
        Returns:
            Dict with operation results
        """
        if action == "send":
            return self.send_email(**kwargs)
        elif action == "read":
            return self.read_emails(**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def send_email(self, to: str, subject: str, body: str, from_addr: str = None, **kwargs) -> Dict[str, Any]:
        """Send an email."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_server = os.getenv("SMTP_SERVER", "smtp-mail.outlook.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_pass:
            return {"error": "SMTP_USER and SMTP_PASSWORD environment variables required"}
        
        from_addr = from_addr or smtp_user
        
        try:
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            return {
                "success": True,
                "to": to,
                "subject": subject,
                "from": from_addr
            }
        except Exception as e:
            return {"error": f"Failed to send email: {str(e)}"}
    
    def read_emails(self, folder: str = "INBOX", limit: int = 10, unread_only: bool = True, **kwargs) -> Dict[str, Any]:
        """Read emails from mailbox."""
        import imaplib
        import email
        from email.header import decode_header
        
        imap_server = os.getenv("IMAP_SERVER", "outlook.office365.com")
        imap_user = os.getenv("IMAP_USER", os.getenv("SMTP_USER"))
        imap_pass = os.getenv("IMAP_PASSWORD", os.getenv("SMTP_PASSWORD"))
        
        if not imap_user or not imap_pass:
            return {"error": "IMAP credentials not set"}
        
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(imap_user, imap_pass)
            mail.select(folder)
            
            search_criteria = "UNSEEN" if unread_only else "ALL"
            status, messages = mail.search(None, search_criteria)
            
            email_ids = messages[0].split()
            emails = []
            
            for email_id in email_ids[-limit:]:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                from_addr = msg.get("From")
                date = msg.get("Date")
                
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                emails.append({
                    "id": email_id.decode(),
                    "from": from_addr,
                    "subject": subject,
                    "date": date,
                    "body": body[:500]  # Truncate body
                })
            
            mail.close()
            mail.logout()
            
            return {
                "success": True,
                "folder": folder,
                "count": len(emails),
                "emails": emails
            }
        except Exception as e:
            return {"error": f"Failed to read emails: {str(e)}"}

"""Send monthly expense summary by email (Gmail SMTP example)."""
import os
from datetime import datetime
import pandas as pd
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")  # App password recommended for Gmail
RECIPIENT = os.getenv("RECIPIENT", EMAIL_USER)
METADATA_CSV = os.getenv("METADATA_CSV", "receipts.csv")


def summary_to_html(summary_df):
    rows = ''.join(f"<tr><td>{row['month']}</td><td style=\"text-align:right\">${row['total']:.2f}</td></tr>" for _,row in summary_df.iterrows())
    return f"""
    <html>
      <body>
        <h2>Monthly Expense Summary</h2>
        <table border="1" cellpadding="6" cellspacing="0">
          <tr><th>Month</th><th>Total</th></tr>
          {rows}
        </table>
      </body>
    </html>
    """


def send_email(subject, html_body):
    if not EMAIL_USER or not EMAIL_PASS:
        raise ValueError("EMAIL_USER and EMAIL_PASS must be set in environment")
    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.set_content("See HTML version of this email")
    msg.add_alternative(html_body, subtype="html")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(EMAIL_USER, EMAIL_PASS)
        s.send_message(msg)


if __name__ == "__main__":
    if not os.path.exists(METADATA_CSV):
        print(f"Metadata file {METADATA_CSV} not found. Run process_receipts.py first.")
        raise SystemExit(1)
    df = pd.read_csv(METADATA_CSV)
    if df.empty:
        print("No receipts recorded.")
        raise SystemExit(0)
    df['date'] = pd.to_datetime(df['date'])
    summary = df.groupby(df['date'].dt.to_period('M'))['total'].sum().sort_index()
    summary_df = summary.reset_index()
    summary_df.columns = ['month','total']
    html = summary_to_html(summary_df)
    subject = f"Monthly Expense Summary - {datetime.now().strftime('%Y-%m-%d')}"
    send_email(subject, html)
    print("Email sent to", RECIPIENT)
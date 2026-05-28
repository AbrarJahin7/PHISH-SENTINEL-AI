import os
from imapclient import IMAPClient
import pyzmail
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
HOST = "imap.gmail.com"

def fetch_emails(limit=10):
    """Fetch up to `limit` recent unread emails from the inbox."""
    emails = []
    with IMAPClient(HOST, ssl=True) as server:
        server.login(EMAIL, PASSWORD)
        server.select_folder("INBOX", readonly=True)  # readonly = don't mark as read
        uids = server.search(['UNSEEN'])               # UNSEEN = unread
        for uid in uids[:limit]:
            raw = server.fetch([uid], ['BODY[]'])
            msg = pyzmail.PyzMessage.factory(raw[uid][b'BODY[]'])
            subject = msg.get_subject() or ""
            sender = msg.get_addresses('from')
            body = ""
            if msg.text_part:
                body = msg.text_part.get_payload().decode(
                    msg.text_part.charset or "utf-8", errors="ignore"
                )
            elif msg.html_part:  # some emails are HTML-only
                body = msg.html_part.get_payload().decode(
                    msg.html_part.charset or "utf-8", errors="ignore"
                )
            emails.append({"subject": subject, "sender": sender, "body": body})
    return emails
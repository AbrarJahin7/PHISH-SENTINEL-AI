"""
Email reader — fetches unread emails from a Gmail-style IMAP mailbox.

Reads credentials in this order:
  1. Arguments passed directly to fetch_emails() (preferred — UI form)
  2. Streamlit Cloud secrets (st.secrets) — for deployed app
  3. .env file / environment variables — for local development

This way the same code works on your laptop AND on Streamlit Cloud.
"""

import os
from imapclient import IMAPClient
import pyzmail
from dotenv import load_dotenv

load_dotenv()  # safe to call — does nothing on the cloud where no .env exists


def _get_secret(name):
    """Try Streamlit secrets first (cloud), then env vars / .env (local)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name)


def fetch_emails(limit=5, email=None, password=None, host="imap.gmail.com"):
    """
    Fetch up to `limit` unread emails.

    Credentials precedence: function args > Streamlit secrets > env vars / .env.

    Raises ValueError if no credentials are found anywhere.
    """
    email = email or _get_secret("EMAIL")
    password = password or _get_secret("PASSWORD")

    if not email or not password:
        raise ValueError(
            "No email credentials provided. Enter your Gmail and App Password in the form."
        )

    # Google shows the 16-char App Password with spaces — strip them.
    password = str(password).replace(" ", "")

    emails = []
    with IMAPClient(host, ssl=True) as server:
        server.login(email, password)
        server.select_folder("INBOX", readonly=True)  # don't mark mail as read
        uids = server.search(['UNSEEN'])
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
            elif msg.html_part:
                body = msg.html_part.get_payload().decode(
                    msg.html_part.charset or "utf-8", errors="ignore"
                )
            emails.append({"subject": subject, "sender": sender, "body": body})
    return emails
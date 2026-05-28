"""
AI detector — uses Google Gemini (free tier, no credit card required).

Reads GEMINI_API_KEY from Streamlit secrets first (cloud), env vars / .env second (local).
Returns a dict {score, verdict, reasons} with the same shape no matter what.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


def _get_secret(name):
    """Try Streamlit secrets first (cloud), then env vars / .env (local)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name)


# Read once at module load
_API_KEY = _get_secret("GEMINI_API_KEY")
_model = None

if _API_KEY:
    try:
        genai.configure(api_key=_API_KEY)
        # Flash is fast, free-tier friendly, and good at classification.
        _model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        _model = None


def analyze_email(subject, body):
    """
    Ask Gemini to judge an email. Returns a dict: {score, verdict, reasons}.
    Never raises — on any failure returns an error dict so the dashboard keeps working.
    """
    if not _model:
        return {
            "score": 0,
            "verdict": "error",
            "reasons": [
                "GEMINI_API_KEY not configured. On Streamlit Cloud, add it under "
                "Settings → Secrets in TOML format: GEMINI_API_KEY = \"your-key\""
            ],
        }

    prompt = f"""You are a cybersecurity analyst. Analyze this email for phishing.

Subject: {subject}

Body:
{body}

Respond with ONLY a JSON object, no other text, in exactly this format:
{{"score": <0-100 integer>, "verdict": "<phishing or safe>", "reasons": ["reason 1", "reason 2"]}}"""

    try:
        response = _model.generate_content(prompt)
        text = response.text.strip()
        # Gemini sometimes wraps JSON in ```json fences — strip them.
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        # Never crash the dashboard. Return a structured error.
        return {
            "score": 0,
            "verdict": "error",
            "reasons": [f"AI call failed: {type(e).__name__}: {str(e)[:200]}"],
        }
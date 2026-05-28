import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# If you added the get_secret helper from config.py, use that instead of os.getenv.
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Flash is fast, free-tier friendly, and good at classification.
model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_email(subject, body):
    """Ask Gemini to judge the email. Returns a dict: score, verdict, reasons.
    Same shape as the OpenAI version, so the rest of the app is unchanged."""
    prompt = f"""You are a cybersecurity analyst. Analyze this email for phishing.

Subject: {subject}

Body:
{body}

Respond with ONLY a JSON object, no other text, in exactly this format:
{{"score": <0-100 integer>, "verdict": "<phishing or safe>", "reasons": ["reason 1", "reason 2"]}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Gemini sometimes wraps JSON in ```json fences — strip them.
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        # Never crash the app if the AI is unavailable — degrade gracefully.
        return {"score": 0, "verdict": "error", "reasons": [f"AI unavailable: {e}"]}
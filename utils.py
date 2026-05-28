import re                  # 're' = regular expressions, for finding patterns in text
import tldextract          # splits a URL into its domain parts

# Words that frequently appear in phishing emails.
SUSPICIOUS_WORDS = [
    "urgent", "verify", "password", "click here", "bank",
    "suspended", "limited time", "login", "confirm", "security alert",
    "act now", "account locked", "wire transfer", "gift card",
]

def count_suspicious_words(text):
    """Return a score and the list of suspicious words found."""
    text_lower = text.lower()          # lowercase so 'Verify' matches 'verify'
    found = [w for w in SUSPICIOUS_WORDS if w in text_lower]
    score = len(found) * 8             # each word adds 8 points
    return score, found

def extract_urls(text):
    """Find every http/https link in the text."""
    return re.findall(r'https?://\S+', text)

def analyze_domains(urls):
    """Flag domains that look like fakes of real brands."""
    # These are 'lookalikes': paypa1 (number 1 instead of l), arnazon (rn looks like m)
    fake_lookalikes = ["paypa1", "arnazon", "micr0soft", "g00gle", "faceb00k", "app1e"]
    suspicious = []
    for url in urls:
        ext = tldextract.extract(url)   # e.g. 'paypa1' from 'http://paypa1.com/login'
        domain = ext.domain
        for fake in fake_lookalikes:
            if fake in domain:
                suspicious.append(domain)
    return suspicious
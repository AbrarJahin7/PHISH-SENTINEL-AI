import os
import joblib

_model = None
_vectorizer = None

def _load():
    """Load the saved model once and keep it in memory."""
    global _model, _vectorizer
    if _model is None:
        if not (os.path.exists("model.pkl") and os.path.exists("vectorizer.pkl")):
            return False
        _model = joblib.load("model.pkl")
        _vectorizer = joblib.load("vectorizer.pkl")
    return True

def ml_predict(text):
    """Return a dict with the ML score and label, or None if no model is trained."""
    if not _load():
        return None
    vec = _vectorizer.transform([text])
    # predict_proba gives confidence per class, e.g. [0.12 safe, 0.88 phishing]
    proba = _model.predict_proba(vec)[0]
    classes = list(_model.classes_)
    # Find the probability assigned to the 'phishing' class, whatever it's labeled.
    phishing_idx = None
    for i, c in enumerate(classes):
        if str(c).lower() in ("phishing", "1", "spam", "phish"):
            phishing_idx = i
    if phishing_idx is None:
        phishing_idx = int(proba.argmax())
    score = round(proba[phishing_idx] * 100)
    label = str(classes[phishing_idx]) if score >= 50 else str(classes[1 - phishing_idx])
    return {"score": score, "label": label}
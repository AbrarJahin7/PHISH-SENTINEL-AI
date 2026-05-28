"""
Scoring engine — fuses signals from three detection layers into a single 0-100 score.

Design philosophy:
  - ML and AI are the "smart" layers (context-aware). They DOMINATE the verdict.
  - Rules and URL checks are "supporting evidence" (transparent but fragile).
  - When AI or ML is offline, the remaining smart layer absorbs its weight.
  - The full weight always sums to 1.0 — no signal is wasted when something is offline.

Base weights when all four are available:
  rules: 10%  | urls: 10%  | ai: 40%  | ml: 40%

Fallback hierarchy (smart layers redistribute first):
  - AI offline → ML jumps to 70%, rules+urls split the remaining 30%
  - ML offline → AI jumps to 70%, rules+urls split the remaining 30%
  - Both AI and ML offline → rules+urls only (degraded mode)
"""


def final_score(keyword_score, url_score, ai_score=None, ml_score=None):
    """
    Fuse layer scores into one 0-100 threat score.

    Args:
        keyword_score: 0-100 from rule engine (always present)
        url_score: 0-100 from URL/domain checks (always present)
        ai_score: 0-100 from LLM, or None if offline/unavailable
        ml_score: 0-100 from trained classifier, or None if not trained

    Returns:
        Integer 0-100.
    """
    # Clamp every input to a sane 0-100 range
    keyword_score = _clamp(keyword_score)
    url_score = _clamp(url_score)
    ai_present = ai_score is not None
    ml_present = ml_score is not None
    if ai_present:
        ai_score = _clamp(ai_score)
    if ml_present:
        ml_score = _clamp(ml_score)

    # ----- Pick the weight profile based on what's available -----
    if ai_present and ml_present:
        # Full stack: ML + AI dominate, rules are supporting evidence.
        w_kw, w_url, w_ai, w_ml = 0.10, 0.10, 0.40, 0.40

    elif ml_present and not ai_present:
        # AI offline → ML inherits AI's authority. ML becomes the brain.
        w_kw, w_url, w_ai, w_ml = 0.15, 0.15, 0.00, 0.70

    elif ai_present and not ml_present:
        # ML not trained → AI carries the smart-layer load alone.
        w_kw, w_url, w_ai, w_ml = 0.15, 0.15, 0.70, 0.00

    else:
        # Degraded: only rules + url checks available.
        # Give URL findings a bit more weight than keyword counts —
        # lookalike domains are a stronger signal than the word "urgent".
        w_kw, w_url, w_ai, w_ml = 0.40, 0.60, 0.00, 0.00

    # ----- Weighted sum -----
    total = (keyword_score * w_kw) + (url_score * w_url)
    if ai_present:
        total += ai_score * w_ai
    if ml_present:
        total += ml_score * w_ml

    return min(100, max(0, round(total)))


def verdict(score):
    """Map a 0-100 score to a human-readable verdict label."""
    if score >= 70:
        return "🔴 PHISHING"
    elif score >= 40:
        return "🟡 SUSPICIOUS"
    else:
        return "🟢 SAFE"


def _clamp(x):
    """Force a number to be in 0-100 range. Defensive — bad inputs shouldn't crash scoring."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0
    if x < 0:
        return 0
    if x > 100:
        return 100
    return x


def explain_weights(ai_score=None, ml_score=None):
    """
    Return which weight profile is active and the per-layer percentages.
    Useful for showing the user *why* the score came out the way it did.

    Returns dict with keys: profile, weights (dict), note (str).
    """
    ai_present = ai_score is not None
    ml_present = ml_score is not None

    if ai_present and ml_present:
        return {
            "profile": "Full stack (AI + ML active)",
            "weights": {"rules": 10, "urls": 10, "ai": 40, "ml": 40},
            "note": "All four layers contributing. AI and ML dominate.",
        }
    if ml_present and not ai_present:
        return {
            "profile": "ML priority (AI offline)",
            "weights": {"rules": 15, "urls": 15, "ai": 0, "ml": 70},
            "note": "AI unavailable → trained ML model carries the verdict.",
        }
    if ai_present and not ml_present:
        return {
            "profile": "AI priority (ML not trained)",
            "weights": {"rules": 15, "urls": 15, "ai": 70, "ml": 0},
            "note": "ML model not loaded → LLM carries the verdict.",
        }
    return {
        "profile": "Degraded (rules only)",
        "weights": {"rules": 40, "urls": 60, "ai": 0, "ml": 0},
        "note": "Both AI and ML offline. Verdict is heuristic-only — treat with caution.",
    }
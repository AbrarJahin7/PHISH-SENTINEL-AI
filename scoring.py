def final_score(keyword_score, url_score, ai_score, ml_score=None):
    if ml_score is None:
        # No trained model yet — use rules + AI only.
        score = (keyword_score * 0.3) + (url_score * 0.3) + (ai_score * 0.4)
    else:
        # With ML: AI and ML are the heavy hitters, rules are supporting evidence.
        score = (keyword_score * 0.15) + (url_score * 0.15) + (ai_score * 0.35) + (ml_score * 0.35)
    return min(round(score), 100)

def verdict(score):
    if score >= 70:
        return "🔴 PHISHING"
    elif score >= 40:
        return "🟡 SUSPICIOUS"
    else:
        return "🟢 SAFE"
"""
SECURITY MINDS PRO — Phishing Email Detector
Built by Abrar Jahin
Hacker-terminal themed dashboard with multi-layer detection.

DROP-IN REPLACEMENT for your existing dashboard.py.
Uses the same files you already have:
  - utils.py        (count_suspicious_words, extract_urls, analyze_domains)
  - detector.py     (analyze_email)
  - scoring.py      (final_score, verdict)
  - email_reader.py (fetch_emails)
  - ml_detector.py  (ml_predict)
"""

import streamlit as st
from utils import count_suspicious_words, extract_urls, analyze_domains
from scoring import final_score, verdict, explain_weights
from detector import analyze_email

# Wrapped so the dashboard still loads even if these files have a problem.
# Same imports as your original dashboard.py, just with safe fallback.
try:
    from ml_detector import ml_predict
    ML_AVAILABLE = True
except Exception:
    ML_AVAILABLE = False
    def ml_predict(_):
        return None

try:
    from email_reader import fetch_emails
    EMAIL_AVAILABLE = True
except Exception:
    EMAIL_AVAILABLE = False
    def fetch_emails(limit=5):
        return []


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SecurityMinds Pro // Phishing Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HACKER TERMINAL THEME (CSS)
# ============================================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&family=VT323&display=swap" rel="stylesheet">

<style>
:root {
  --bg-0: #000000;
  --bg-1: #050a05;
  --bg-2: #0a140a;
  --grid: rgba(0, 255, 65, 0.04);
  --green-dim: #1a5c1a;
  --green-mid: #00b14f;
  --green-bright: #00ff41;
  --amber: #ffb000;
  --red: #ff003c;
  --text: #c7ffcd;
  --text-dim: #5a8a5a;
  --mono: 'JetBrains Mono', 'Courier New', monospace;
  --crt: 'VT323', monospace;
}

.stApp {
  background:
    radial-gradient(ellipse at top, rgba(0, 255, 65, 0.08), transparent 60%),
    radial-gradient(ellipse at bottom, rgba(0, 255, 65, 0.05), transparent 60%),
    linear-gradient(180deg, var(--bg-0), var(--bg-1));
  background-attachment: fixed;
  color: var(--text);
  font-family: var(--mono);
}

.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
  z-index: 0;
  animation: gridShift 30s linear infinite;
}

.stApp::after {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 255, 65, 0.03),
    rgba(0, 255, 65, 0.03) 1px,
    transparent 1px,
    transparent 3px
  );
  pointer-events: none;
  z-index: 1;
  mix-blend-mode: overlay;
}

@keyframes gridShift {
  0% { transform: translate(0, 0); }
  100% { transform: translate(32px, 32px); }
}

/* ============================================================
   GLOBAL FONT — monospace everywhere
   ============================================================ */
h1, h2, h3, h4, h5, h6, p, div, span, label, li {
  font-family: var(--mono) !important;
  color: var(--text);
}

/* ============================================================
   EXPANDER ICON FIX
   --------------------------------------------------------------
   Streamlit's expander chevron is a Material Symbols ligature
   span like "keyboard_arrow_right". When our global monospace
   override hits it, the ligature breaks and the literal text
   ("arrow_right" / "arrow_down") leaks into the header.

   Fix: hide every possible icon container inside the expander
   header, then draw our own pure-CSS triangle that rotates when
   the expander is open. Works on every Streamlit version because
   we don't depend on knowing the icon's class name.
   ============================================================ */

/* Nuke every icon variant Streamlit might use inside an expander header */
[data-testid="stExpander"] summary svg,
[data-testid="stExpander"] summary [data-testid*="icon" i],
[data-testid="stExpander"] summary [data-testid*="Icon"],
[data-testid="stExpander"] summary [class*="icon" i],
[data-testid="stExpander"] summary [class*="Icon"],
[data-testid="stExpander"] summary [class*="material" i],
[data-testid="stExpander"] summary [class*="Material"],
[data-testid="stExpander"] summary i,
.streamlit-expanderHeader svg,
.streamlit-expanderHeader [data-testid*="icon" i],
.streamlit-expanderHeader [class*="icon" i],
.streamlit-expanderHeader [class*="material" i],
.streamlit-expanderHeader i {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  visibility: hidden !important;
}

/* Hide the default native disclosure marker too */
[data-testid="stExpander"] summary::-webkit-details-marker,
[data-testid="stExpander"] summary::marker { display: none !important; }

/* Draw our own chevron with pure CSS — a rotated triangle.
   We use ::before so the user's label text is untouched. */
[data-testid="stExpander"] summary,
.streamlit-expanderHeader {
  list-style: none !important;
  display: flex !important;
  align-items: center !important;
  gap: 0.8rem !important;
  padding-left: 1rem !important;
  cursor: pointer !important;
}

[data-testid="stExpander"] summary::before,
.streamlit-expanderHeader::before {
  content: "▶";
  display: inline-block;
  color: var(--green-bright);
  font-size: 0.7rem;
  font-family: var(--mono) !important;
  transition: transform 0.2s ease;
  text-shadow: 0 0 6px var(--green-bright);
  flex-shrink: 0;
}

/* When the expander is open, rotate the chevron to point down */
[data-testid="stExpander"] details[open] > summary::before,
[data-testid="stExpander"]:has(details[open]) summary::before {
  transform: rotate(90deg);
}

h1 {
  color: var(--green-bright) !important;
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.6), 0 0 24px rgba(0, 255, 65, 0.25);
  letter-spacing: 0.05em;
  font-weight: 700 !important;
}

h2, h3 {
  color: var(--green-mid) !important;
  border-left: 3px solid var(--green-bright);
  padding-left: 0.6rem;
  margin-top: 1.5rem !important;
  text-shadow: 0 0 4px rgba(0, 255, 65, 0.4);
}

.brand-banner {
  position: relative;
  border: 1px solid var(--green-dim);
  background: linear-gradient(135deg, rgba(0, 255, 65, 0.04), rgba(0, 0, 0, 0.6));
  padding: 1.4rem 1.6rem;
  margin-bottom: 1.2rem;
  overflow: hidden;
}

.brand-banner::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--green-bright), transparent);
  animation: scanLine 4s linear infinite;
}

@keyframes scanLine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.brand-logo {
  font-family: var(--crt);
  font-size: 2.6rem;
  line-height: 1;
  color: var(--green-bright);
  text-shadow: 0 0 12px rgba(0, 255, 65, 0.7);
  letter-spacing: 0.08em;
  margin: 0;
}

.brand-platform {
  display: inline-block;
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.35em;
  color: #000;
  background: var(--green-bright);
  padding: 0.15rem 0.6rem;
  margin-bottom: 0.4rem;
  text-transform: uppercase;
  font-weight: 700;
  box-shadow: 0 0 8px rgba(0, 255, 65, 0.5);
}

/* ============================================================
   SCROLLING MARQUEE TICKER
   ============================================================ */
.marquee {
  position: relative;
  width: 100%;
  overflow: hidden;
  border: 1px solid var(--green-dim);
  border-left: 3px solid var(--green-bright);
  background: linear-gradient(90deg, rgba(0, 255, 65, 0.08), rgba(0, 0, 0, 0.6));
  padding: 0.55rem 0;
  margin-bottom: 1rem;
  font-family: var(--mono);
}

.marquee::before,
.marquee::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 60px;
  z-index: 2;
  pointer-events: none;
}
.marquee::before { left: 0;  background: linear-gradient(90deg, #000, transparent); }
.marquee::after  { right: 0; background: linear-gradient(-90deg, #000, transparent); }

.marquee-track {
  display: inline-flex;
  white-space: nowrap;
  animation: marqueeScroll 45s linear infinite;
}

.marquee-content {
  color: var(--green-bright);
  font-size: 0.8rem;
  letter-spacing: 0.18em;
  text-shadow: 0 0 4px rgba(0, 255, 65, 0.5);
  padding-right: 1rem;
}

@keyframes marqueeScroll {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.brand-tag {
  color: var(--text-dim);
  font-size: 0.82rem;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  margin-top: 0.4rem;
}

.brand-meta {
  display: flex;
  gap: 1.4rem;
  margin-top: 0.9rem;
  font-size: 0.78rem;
  color: var(--text-dim);
  flex-wrap: wrap;
}

.brand-meta span b {
  color: var(--green-mid);
  font-weight: 500;
}

.cursor {
  display: inline-block;
  width: 0.6rem;
  height: 1.1rem;
  background: var(--green-bright);
  margin-left: 0.3rem;
  animation: blink 1s steps(2) infinite;
  vertical-align: middle;
  box-shadow: 0 0 8px var(--green-bright);
}

@keyframes blink {
  50% { opacity: 0; }
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #000000, #030803) !important;
  border-right: 1px solid var(--green-dim);
}

section[data-testid="stSidebar"] * {
  color: var(--text) !important;
  font-family: var(--mono) !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  color: var(--green-bright) !important;
  border-left: 2px solid var(--green-bright);
  padding-left: 0.5rem;
}

.stTextArea textarea, .stTextInput input {
  background: var(--bg-2) !important;
  color: var(--green-bright) !important;
  border: 1px solid var(--green-dim) !important;
  border-radius: 0 !important;
  font-family: var(--mono) !important;
  caret-color: var(--green-bright);
}

.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: var(--green-bright) !important;
  box-shadow: 0 0 0 1px var(--green-bright), 0 0 12px rgba(0, 255, 65, 0.3) !important;
  outline: none !important;
}

.stTextArea label, .stTextInput label {
  color: var(--green-mid) !important;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-size: 0.78rem !important;
}

.stButton > button {
  background: transparent !important;
  color: var(--green-bright) !important;
  border: 1px solid var(--green-bright) !important;
  border-radius: 0 !important;
  font-family: var(--mono) !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  padding: 0.6rem 1.4rem !important;
  transition: all 0.18s ease;
}

.stButton > button:hover {
  background: var(--green-bright) !important;
  color: #000000 !important;
  box-shadow: 0 0 16px rgba(0, 255, 65, 0.55), inset 0 0 8px rgba(0, 0, 0, 0.4);
}

.stButton > button:before {
  content: '> ';
  color: inherit;
}

.stRadio > div { background: transparent; }
.stRadio label { color: var(--text) !important; }
.stRadio [data-baseweb="radio"] div:first-child {
  border-color: var(--green-mid) !important;
}

[data-testid="stMetricValue"] {
  color: var(--green-bright) !important;
  font-family: var(--crt) !important;
  font-size: 3.6rem !important;
  text-shadow: 0 0 16px rgba(0, 255, 65, 0.6);
}

[data-testid="stMetricLabel"] {
  color: var(--text-dim) !important;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-size: 0.75rem !important;
}

.streamlit-expanderHeader {
  background: var(--bg-2) !important;
  border: 1px solid var(--green-dim) !important;
  color: var(--green-mid) !important;
  font-family: var(--mono) !important;
  border-radius: 0 !important;
}

.streamlit-expanderHeader:hover {
  border-color: var(--green-bright) !important;
  color: var(--green-bright) !important;
}

.tech-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0.8rem 0 0.4rem 0;
}

.tech-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.7rem;
  border: 1px solid var(--green-dim);
  background: rgba(0, 255, 65, 0.04);
  color: var(--green-mid);
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--mono);
}

.tech-pill.active {
  border-color: var(--green-bright);
  color: var(--green-bright);
  box-shadow: 0 0 8px rgba(0, 255, 65, 0.4);
  background: rgba(0, 255, 65, 0.08);
}

.tech-pill.idle {
  border-color: #3a3a3a;
  color: #555555;
  background: transparent;
}

.dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  display: inline-block;
}

.dot.green { background: var(--green-bright); box-shadow: 0 0 6px var(--green-bright); animation: pulse 2s infinite; }
.dot.gray  { background: #444; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.layer-card {
  border: 1px solid var(--green-dim);
  background: linear-gradient(135deg, rgba(0, 255, 65, 0.03), rgba(0, 0, 0, 0.4));
  padding: 1rem 1.2rem;
  margin-bottom: 0.8rem;
}

.layer-card .layer-title {
  color: var(--green-mid);
  font-size: 0.78rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.layer-card .layer-value {
  color: var(--green-bright);
  font-family: var(--crt);
  font-size: 1.8rem;
  line-height: 1;
}

.layer-card .layer-detail {
  color: var(--text-dim);
  font-size: 0.8rem;
  margin-top: 0.4rem;
}

.verdict-banner {
  text-align: center;
  padding: 1.4rem;
  margin: 1rem 0;
  font-family: var(--crt);
  font-size: 2.2rem;
  letter-spacing: 0.15em;
  border: 1px solid;
  position: relative;
  overflow: hidden;
}

.verdict-safe   { color: var(--green-bright); border-color: var(--green-bright); text-shadow: 0 0 12px var(--green-bright); }
.verdict-warn   { color: var(--amber); border-color: var(--amber); text-shadow: 0 0 12px var(--amber); }
.verdict-danger { color: var(--red); border-color: var(--red); text-shadow: 0 0 12px var(--red); animation: dangerPulse 1.5s ease-in-out infinite; }

@keyframes dangerPulse {
  0%, 100% { box-shadow: 0 0 0 rgba(255, 0, 60, 0); }
  50%      { box-shadow: 0 0 30px rgba(255, 0, 60, 0.4), inset 0 0 30px rgba(255, 0, 60, 0.1); }
}

.boot {
  font-family: var(--mono);
  color: var(--green-mid);
  font-size: 0.82rem;
  line-height: 1.8;
  margin: 0.6rem 0 1.2rem 0;
  white-space: pre-wrap;
}

.boot .ok   { color: var(--green-bright); }
.boot .warn { color: var(--amber); }

pre, code {
  background: #000 !important;
  border: 1px solid var(--green-dim) !important;
  color: var(--green-bright) !important;
  font-family: var(--mono) !important;
}

#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.5rem; max-width: 1200px; }

div[data-testid="stAlert"] {
  background: var(--bg-2) !important;
  border: 1px solid var(--amber) !important;
  border-radius: 0 !important;
  color: var(--amber) !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def brand_banner():
    st.markdown("""
    <div class="brand-banner">
      <div class="brand-platform">SECURITY MINDS PRO</div>
      <div class="brand-logo">PHISH&nbsp;SENTINEL<span class="cursor"></span></div>
      <div class="brand-tag">// Multi-Layer Phishing Email Defense · A Security Minds Pro Project</div>
      <div class="brand-meta">
        <span>STUDENT <b>ABRAR JAHIN</b></span>
        <span>SUBMITTED TO <b>MASHIHOOR SIR</b></span>
        <span>PLATFORM <b>SECURITY MINDS PRO</b></span>
        <span>BUILD <b>v1.0.0</b></span>
        <span>STATUS <b style="color:#00ff41;">● ONLINE</b></span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def marquee():
    """Scrolling status ticker shown on the home/scan page."""
    items = [
        "▸ SECURITY MINDS PRO",
        "▸ STUDENT: ABRAR JAHIN",
        "▸ SUBMITTED TO: MASHIHOOR SIR",
        "▸ STACK: PYTHON · STREAMLIT · OPENAI · SCIKIT-LEARN · TF-IDF · LOGISTIC REGRESSION",
        "▸ DETECTION: RULE ENGINE + LLM + ML CLASSIFIER",
        "▸ EMAIL INTAKE: IMAPCLIENT · PYZMAIL36 · GMAIL APP PASSWORDS",
        "▸ ML DATASET: KAGGLE PHISHING EMAIL DETECTION (CYBER COP)",
        "▸ STATUS: ONLINE",
    ]
    # Duplicate the content so the scroll loops seamlessly
    content = "&nbsp;&nbsp;&nbsp;".join(items)
    st.markdown(f"""
    <div class="marquee">
      <div class="marquee-track">
        <span class="marquee-content">{content}&nbsp;&nbsp;&nbsp;</span>
        <span class="marquee-content">{content}&nbsp;&nbsp;&nbsp;</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def boot_sequence():
    ml_status = '<span class="ok">[OK]</span>  loading ML classifier ......... ready' if ML_AVAILABLE \
        else '<span class="warn">[..]</span>  loading ML classifier ......... not trained'
    email_status = '<span class="ok">[OK]</span>  loading inbox reader .......... ready' if EMAIL_AVAILABLE \
        else '<span class="warn">[..]</span>  loading inbox reader .......... not configured'
    st.markdown(f"""
    <div class="boot">
<span class="ok">[OK]</span>  initializing securityminds pro v1.0.0
<span class="ok">[OK]</span>  loading rule engine ........... ready
<span class="ok">[OK]</span>  loading ai detector (LLM) ..... ready
{ml_status}
{email_status}
<span class="ok">[OK]</span>  loading scoring fusion ........ ready
<span class="warn">[..]</span>  awaiting target email ......... standby
    </div>
    """, unsafe_allow_html=True)


def tech_stack_strip(active_layers):
    pills = ""
    for name in ["RULES", "AI / LLM", "ML MODEL"]:
        on = active_layers.get(name, False)
        cls = "active" if on else "idle"
        dot = "green" if on else "gray"
        pills += f'<span class="tech-pill {cls}"><span class="dot {dot}"></span>{name}</span>'
    st.markdown(f'<div class="tech-row">{pills}</div>', unsafe_allow_html=True)


def layer_card(title, value, detail=""):
    st.markdown(f"""
    <div class="layer-card">
      <div class="layer-title">{title}</div>
      <div class="layer-value">{value}</div>
      <div class="layer-detail">{detail}</div>
    </div>
    """, unsafe_allow_html=True)


def render_verdict(score):
    """Reads your scoring.verdict() output (which contains emoji markers) and themes it."""
    label = verdict(score)
    if "PHISHING" in label or "🔴" in label:
        cls, txt = "verdict-danger", "⚠  PHISHING DETECTED  ⚠"
    elif "SUSPICIOUS" in label or "🟡" in label:
        cls, txt = "verdict-warn", "⚡  SUSPICIOUS — REVIEW  ⚡"
    else:
        cls, txt = "verdict-safe", "✓  EMAIL APPEARS SAFE  ✓"
    st.markdown(f'<div class="verdict-banner {cls}">{txt}</div>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR — NAVIGATION
# ============================================================
with st.sidebar:
    st.markdown("### `> NAVIGATION`")
    page = st.radio(
        "MODE",
        ["⌬ Scan Email", "⌬ Inbox Monitor", "⌬ Learn the Project", "⌬ Tech Stack", "⌬ About"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### `> DETECTION LAYERS`")
    st.markdown("""
- **Layer 1 —** Rule Engine
- **Layer 2 —** AI / LLM Analysis
- **Layer 3 —** ML Classifier
- **Fusion  —** Weighted Score
""")

    st.markdown("---")
    st.markdown("### `> SESSION`")
    if "scans" not in st.session_state:
        st.session_state.scans = 0
    st.markdown(f"Scans performed: **{st.session_state.scans}**")

    st.markdown("---")
    st.markdown(
        "<div style='color:#5a8a5a; font-size:0.7rem; letter-spacing:0.15em; line-height:1.6;'>"
        "A PROJECT BY<br>"
        "<b style='color:#00ff41;'>ABRAR JAHIN</b><br>"
        "STUDENT @ SECURITY MINDS PRO<br><br>"
        "SUBMITTED TO<br>"
        "<b style='color:#00b14f;'>MASHIHOOR SIR</b>"
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# PAGE 1 — SCAN EMAIL  (matches your original "Paste email" logic exactly)
# ============================================================
def page_scan():
    brand_banner()
    marquee()
    boot_sequence()

    st.markdown("## `> target_input`")
    st.markdown(
        "<p style='color:#5a8a5a; font-size:0.85rem;'>"
        "Paste a suspicious email below. The system will analyze it across three detection "
        "layers and fuse the results.</p>",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([2, 1])
    with col_a:
        email_text = st.text_area("EMAIL BODY", height=260, key="body_in",
                                  placeholder="paste raw email content here...")
    with col_b:
        subject = st.text_input("SUBJECT", value="", key="subj_in",
                                placeholder="optional")
        st.markdown(" ")
        run = st.button("EXECUTE SCAN")

    if run:
        if not email_text.strip():
            st.warning("[!] no input detected. paste an email to continue.")
            return

        st.session_state.scans += 1

        with st.spinner("> running multi-layer analysis..."):
            # Layer 1 — Rules  (your utils.py)
            keyword_score, words = count_suspicious_words(email_text)
            urls = extract_urls(email_text)
            bad_domains = analyze_domains(urls)
            url_score = len(bad_domains) * 25

            # Layer 2 — AI  (your detector.py)
            ai = analyze_email(subject, email_text)
            ai_offline = ai.get("verdict") in (None, "error")
            # Pass None (not 0) when AI is offline so scoring.py can redistribute weight to ML.
            ai_score = None if ai_offline else ai.get("score", 0)

            # Layer 3 — ML  (your ml_detector.py)
            ml = ml_predict(email_text)
            ml_score = ml["score"] if ml else None

            # Fusion — dynamic weighting based on which layers are available
            total = final_score(keyword_score, url_score, ai_score, ml_score)

        st.markdown("## `> analysis_complete`")

        tech_stack_strip({
            "RULES": True,
            "AI / LLM": ai.get("verdict") not in (None, "error"),
            "ML MODEL": ml is not None,
        })

        render_verdict(total)

        st.markdown("### `> per_layer_breakdown`")
        c1, c2, c3 = st.columns(3)
        with c1:
            layer_card(
                "L1 · RULE ENGINE",
                f"{min(keyword_score + url_score, 100)}/100",
                f"keywords: {len(words)} · suspicious domains: {len(bad_domains)}",
            )
        with c2:
            layer_card(
                "L2 · AI / LLM",
                f"{ai_score}/100" if ai.get("verdict") not in (None, "error") else "OFFLINE",
                str(ai.get("verdict", "no response")).upper(),
            )
        with c3:
            if ml:
                layer_card(
                    "L3 · ML MODEL",
                    f"{ml_score}/100",
                    f"classifier label: {ml['label']}",
                )
            else:
                layer_card(
                    "L3 · ML MODEL",
                    "NOT TRAINED",
                    "run train_model.py to enable",
                )

        st.markdown("### `> fused_score`")
        st.metric("THREAT SCORE", f"{total}/100")

        # Show which weight profile fired — explains *why* the score came out this way
        wp = explain_weights(ai_score=ai_score, ml_score=ml_score)
        profile_color = "var(--green-bright)" if "Full stack" in wp["profile"] else (
            "var(--amber)" if "Degraded" in wp["profile"] else "var(--green-mid)"
        )
        weights_html = " · ".join(
            f"<span style='color:{profile_color};'>{k.upper()} {v}%</span>"
            for k, v in wp["weights"].items() if v > 0
        )
        st.markdown(f"""
        <div class="layer-card" style="border-left:3px solid {profile_color};">
          <div class="layer-title" style="color:{profile_color};">▸ SCORING PROFILE · {wp['profile']}</div>
          <div class="layer-detail" style="color:#c7ffcd; font-size:0.85rem; margin-bottom:6px;">{wp['note']}</div>
          <div style="font-family:var(--mono); font-size:0.82rem; letter-spacing:0.1em;">{weights_html}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### `> evidence`")
        e1, e2 = st.columns(2)
        with e1:
            with st.expander("🔍 Rule-Based Evidence", expanded=True):
                st.markdown(f"**Suspicious keywords found:** {len(words)}")
                st.code(", ".join(words) if words else "(none)")
                st.markdown(f"**URLs extracted:** {len(urls)}")
                st.code("\n".join(urls) if urls else "(none)")
                st.markdown(f"**Lookalike domains:** {len(bad_domains)}")
                st.code(", ".join(bad_domains) if bad_domains else "(none)")
        with e2:
            with st.expander("🤖 AI Reasoning", expanded=True):
                st.markdown(f"**Verdict:** `{ai.get('verdict', 'n/a')}`")
                st.markdown("**Reasons cited:**")
                for r in ai.get("reasons", []) or ["(no reasons returned)"]:
                    st.markdown(f"- {r}")


# ============================================================
# PAGE 2 — INBOX MONITOR  (matches your original "Scan my inbox" logic exactly)
# ============================================================
def page_inbox():
    brand_banner()
    st.markdown("## `> inbox_monitor`")
    st.markdown(
        "<p style='color:#5a8a5a;'>Enter your Gmail credentials below. The system will "
        "pull your unread emails and scan each one with all three detection layers. "
        "<b style='color:#ffb000;'>Your credentials are used only for this scan and never stored.</b></p>",
        unsafe_allow_html=True,
    )

    if not EMAIL_AVAILABLE:
        st.warning("[!] email_reader.py is not available.")
        return

    # ============== CREDENTIAL FORM ==============
    st.markdown("### `> credentials`")
    st.markdown(
        """
<div class="layer-card" style="border-left:3px solid var(--amber);">
  <div class="layer-title" style="color:var(--amber);">▸ PRIVACY NOTICE</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.85rem;">
    Your credentials are used <b>only</b> for this single scan and are never stored
    or logged. They live in memory for the duration of the request and disappear
    when the page reloads. For your safety, use a <b>Gmail App Password</b> — not
    your real Gmail password.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.form("inbox_form", clear_on_submit=False):
        user_email = st.text_input(
            "GMAIL ADDRESS",
            placeholder="yourname@gmail.com",
            key="inbox_email",
        )
        user_password = st.text_input(
            "GMAIL APP PASSWORD (16 characters)",
            type="password",
            placeholder="xxxx xxxx xxxx xxxx",
            help="Generate one at myaccount.google.com/apppasswords (requires 2-Step Verification enabled).",
            key="inbox_pass",
        )
        limit = st.slider("HOW MANY UNREAD EMAILS TO SCAN", 1, 10, 5, key="inbox_limit")
        submitted = st.form_submit_button("FETCH & SCAN UNREAD")

    with st.expander("❓ How do I get a Gmail App Password?"):
        st.markdown("""
1. Go to **[myaccount.google.com/security](https://myaccount.google.com/security)** and
   enable **2-Step Verification** (required by Google before App Passwords can be generated).
2. Visit **[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**.
3. Name the app anything (e.g. "Phish Sentinel"), click **Create**.
4. Google shows you a **16-character password** like `abcd efgh ijkl mnop`.
5. Copy it and paste into the field above. Spaces are fine — we strip them automatically.
6. This password is **scoped to this one app** and can be revoked anytime from the
   App Passwords page without changing your real Gmail password.
""")

    if not submitted:
        return

    if not user_email or not user_password:
        st.warning("[!] please enter both your Gmail address and App Password.")
        return

    # ============== FETCH & SCAN ==============
    with st.spinner("> connecting to imap server..."):
        try:
            inbox = fetch_emails(
                limit=limit,
                email=user_email,
                password=user_password,
            )
        except Exception as e:
            err = str(e).lower()
            if "authentication" in err or "invalid credentials" in err or "login failed" in err:
                st.error(
                    "[!] login failed. Double-check that:\n"
                    "  • the email address is correct\n"
                    "  • you're using a Gmail **App Password**, not your normal password\n"
                    "  • 2-Step Verification is enabled on the Google account"
                )
            else:
                st.error(f"[!] connection failed: {e}")
            return

    if not inbox:
        st.info("[i] no unread emails found in that inbox.")
        return

    st.success(f"[✓] fetched {len(inbox)} unread email(s). running analysis...")

    for i, mail in enumerate(inbox, 1):
        st.session_state.scans += 1

        kw_score, words = count_suspicious_words(mail["body"])
        urls = extract_urls(mail["body"])
        bad_domains = analyze_domains(urls)
        ai = analyze_email(mail["subject"], mail["body"])
        ai_offline = ai.get("verdict") in (None, "error")
        ai_score = None if ai_offline else ai.get("score", 0)
        ml = ml_predict(mail["body"])
        ml_score = ml["score"] if ml else None
        total = final_score(kw_score, len(bad_domains) * 25, ai_score, ml_score)

        with st.expander(f"[{i:02d}] {verdict(total)} — {mail['subject'][:80]}"):
            render_verdict(total)
            st.metric("Threat Score", f"{total}/100")
            st.write("**From:**", mail["sender"])
            st.write("**Suspicious words:**", words or "none")
            st.write("**URLs found:**", urls or "none")
            st.write("**Fake-looking domains:**", bad_domains or "none")
            if ml:
                st.write(
                    "**ML model:**",
                    f"{ml['label']} ({ml['score']}% phishing confidence)"
                )
            st.write("**AI verdict:**", ai.get("verdict", "n/a"))
            st.write("**AI reasons:**")
            for r in ai.get("reasons", []) or ["(none)"]:
                st.write("-", r)


# ============================================================
# PAGE 3 — LEARN THE PROJECT
# ============================================================
def page_learn():
    brand_banner()
    st.markdown("## `> learn_the_project`")
    st.markdown(
        "<p style='color:#5a8a5a;'>Everything this system does, explained from zero. "
        "Pick a section and read in order — or jump around.</p>",
        unsafe_allow_html=True,
    )

    with st.expander("1. What is phishing, and why does it need automation?", expanded=True):
        st.markdown("""
**Phishing** is a social-engineering attack: an email is crafted to trick you into clicking a
malicious link, handing over a password, or transferring money. It is the #1 entry point for
almost every major data breach.

Humans miss phishing emails because attackers exploit *urgency* ("your account will be
suspended in 24 hours"), *authority* ("from: IT department"), and *fear*. Automation helps
because a program does not panic, does not get tired, and does not skip the URL hovering check.

This project automates that check using **three independent layers** so no single weak signal
decides the verdict.
""")

    with st.expander("2. The three detection layers (the core idea)"):
        st.markdown("""
| Layer | What it does | Strength | Weakness |
|---|---|---|---|
| **L1 · Rules** | Looks for specific words ("verify", "urgent") and fake-looking domains (`paypa1.com`). | Fast, free, transparent, explainable. | Easy to bypass with different wording. |
| **L2 · AI / LLM** | A large language model reads the email like a human would and judges intent. | Catches new and creative attacks. | Costs API calls; can hallucinate. |
| **L3 · ML Model** | A classifier *you* train on labeled phishing/safe datasets. | Free to run, offline, learns from data. | Only as good as the dataset. |
| **Fusion** | Weighted average of all three. | No single layer can be wrong alone. | Needs tuning of weights. |

This stacked approach is called **defense in depth** in security — the exact same idea behind
real enterprise email security products.
""")

    with st.expander("3. Layer 1 — How rule-based detection works"):
        st.markdown("""
We keep a list of **suspicious words** (`urgent`, `verify`, `password`, `bank`, ...) and count
how many appear in the email. Each one adds points to the score.

We also extract every URL using a **regular expression** — a tiny pattern language for matching
text:

```python
re.findall(r'https?://\\S+', text)
```

For each URL we pull out the domain with `tldextract` and check it against **lookalike**
domains like `paypa1` (number 1 instead of letter l) or `arnazon` (r+n looks like m on screen).
Real attackers buy these domains constantly.

**Why this matters:** rules are 100% explainable. When the rule layer flags something, you can
show the user *exactly* which words/URLs triggered it.
""")

    with st.expander("4. Layer 2 — How AI / LLM detection works"):
        st.markdown("""
We send the email to a Large Language Model (OpenAI, Google Gemini, Groq, etc.) with a prompt
asking it to behave like a security analyst and return a structured **JSON** verdict:

```json
{"score": 85, "verdict": "phishing",
 "reasons": ["impersonates a bank", "urgent action language", "mismatched sender"]}
```

Why JSON? Because we need the **number** to feed into scoring. If we asked the AI for a
paragraph, we'd be parsing English to find a score — fragile and error-prone.

We set `temperature=0` so the AI gives consistent answers, not creative ones. For phishing
detection we want predictability, not poetry.
""")

    with st.expander("5. Layer 3 — How machine learning works (plain English)"):
        st.markdown("""
**Machine learning** = teaching a program by showing it thousands of examples instead of
writing rules by hand.

Our pipeline has two pieces:

**1. Vectorizer (TF-IDF)** — Models only understand numbers, not words. TF-IDF turns each
email into a vector of numbers, where each number says "how important is this word in this
email, compared to all emails?" Common words like *the* get low scores. Distinctive words
like *verify* get high scores.

**2. Classifier (Logistic Regression)** — Looks at those numbers and learns a formula that
separates *phishing* from *safe*. Logistic Regression is simple and surprisingly strong for
text.

**The golden rule: train/test split.** We hide 20% of the data from the model during training,
then test on that hidden 20%. If we tested on what the model already saw, it would just
memorize answers and look perfect while being useless on new emails. This mistake is called
**data leakage** and it's the #1 reason ML projects look great in lectures but fail in real life.

---

### Dataset used for training

The ML model in this project was trained on the **Phishing Email Detection** dataset
published by *Cyber Cop* on Kaggle:

🔗 [kaggle.com/datasets/subhajournal/phishingemails](https://www.kaggle.com/datasets/subhajournal/phishingemails)

The dataset provides labeled email text bodies — phishing vs. safe — assembled specifically
for training text-analytics classifiers. From the dataset description:

> *"Phishing emails have become a significant threat to individuals and organizations
> worldwide. These deceptive emails aim to trick recipients into divulging sensitive
> information or performing harmful actions. The dataset specifies the email text body and
> the type of emails which can be used to detect phishing emails by extensive analytics of
> the email text and classifying those using machine learning."*

Using a real-world labeled dataset (instead of toy samples) is what lets the trained
classifier generalize to emails it has never seen before.
""")

    with st.expander("6. How the scores are fused (smart, dynamic weighting)"):
        st.markdown("""
Each layer outputs a 0–100 score. We blend them with **weights that adapt to what's
available**, so no signal is ever wasted when a layer goes offline.

**Design philosophy:** the *smart* layers (AI and ML) should dominate the verdict. The
*supporting* layers (keywords and URLs) should corroborate, never override.

| Situation | Rules | URLs | AI / LLM | ML Model |
|---|---|---|---|---|
| Full stack (all 4 active) | 10% | 10% | **40%** | **40%** |
| AI offline → ML takes the wheel | 15% | 15% | — | **70%** |
| ML not trained → AI takes the wheel | 15% | 15% | **70%** | — |
| Both AI and ML offline (degraded) | 40% | 60% | — | — |

When AI fails, its weight doesn't vanish — **ML inherits it** (jumps from 40% to 70%).
Same the other way. Rules and URLs only become primary when both intelligent layers
are unavailable, and even then we warn the user the verdict is heuristic-only.

Final score maps to a verdict:

- `0–39`  → 🟢 SAFE
- `40–69` → 🟡 SUSPICIOUS
- `70–100` → 🔴 PHISHING

You'll see the **active weight profile** displayed on every scan result — so you always
know *why* the score came out the way it did.
""")

    with st.expander("7. Reading real Gmail (IMAP + App Passwords)"):
        st.markdown("""
**IMAP** is the protocol email programs use to read a mailbox. We connect to
`imap.gmail.com`, list unread emails, and pull the subject/sender/body for each.

Gmail does not allow scripts to log in with your normal password. Instead you generate a
**16-character App Password** at
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (after enabling
2-Step Verification). This special password is scoped to this one app and can be revoked
anytime without changing your main password.

We open the mailbox **read-only** so scanning doesn't accidentally mark your unread emails
as read.
""")

    with st.expander("8. Why we use .env files and a .gitignore"):
        st.markdown("""
**Never put secrets (API keys, passwords) directly in your code.** If you push code to
GitHub, the world sees them — and bots scrape GitHub for leaked keys within minutes.

We use a `.env` file to hold secrets locally, and a `.gitignore` file that tells Git
"never upload these." This single habit prevents the #1 beginner security mistake.

On Streamlit Cloud there is no `.env` file — instead you paste secrets into
**Advanced settings → Secrets**. A `config.py` helper lets the same code read from both places.
""")

    with st.expander("9. Going further — real enterprise add-ons"):
        st.markdown("""
What turns this from a class project into a real product:

- **SPF / DKIM / DMARC checks** — cryptographic proof an email actually came from who it claims.
- **VirusTotal API** — check URLs/attachments against known malicious databases.
- **Confusion matrix & better metrics** — measure where your model is wrong, not just how often.
- **Retrain on your own labeled mail** — the model adapts to your specific inbox over time.
- **Chrome extension front-end** — call your deployed API from inside Gmail itself.
- **SIEM integration** — push verdicts to a Security Operations Center alerting pipeline.

Each is a self-contained next step. Add them one at a time.
""")


# ============================================================
# PAGE 4 — TECH STACK
# ============================================================
def page_tech():
    brand_banner()
    st.markdown("## `> technology_stack`")
    st.markdown(
        "<p style='color:#5a8a5a;'>What this system is built with, layer by layer.</p>",
        unsafe_allow_html=True,
    )

    sections = [
        ("LANGUAGE & RUNTIME", [
            ("Python 3.11+", "Core language. Chosen for its data science and AI ecosystem."),
            ("Virtual Environment (venv)", "Isolated dependency sandbox per project."),
        ]),
        ("L1 · RULE ENGINE", [
            ("re (regex)", "Pattern matching to extract URLs and suspicious phrases."),
            ("tldextract", "Splits URLs into subdomain / domain / suffix for lookalike checks."),
            ("validators", "Sanity-checks URL structure."),
        ]),
        ("L2 · AI / LLM", [
            ("OpenAI API (gpt-4o-mini)", "Default LLM provider — paid, high quality."),
            ("Google Gemini (Flash)", "Free alternative — no credit card needed."),
            ("Groq / OpenRouter", "Other free LLM providers, drop-in compatible."),
            ("Prompt engineering", "Structured JSON output for deterministic scoring."),
        ]),
        ("L3 · MACHINE LEARNING", [
            ("scikit-learn", "Classic ML library — TF-IDF + Logistic Regression."),
            ("pandas", "Tabular data handling for the training dataset."),
            ("joblib", "Saves the trained model as model.pkl for reuse."),
            ("Train/test split", "Honest evaluation — prevents data leakage."),
            ("Kaggle Dataset · Cyber Cop",
             "Phishing Email Detection — labeled email-body corpus. Source: kaggle.com/datasets/subhajournal/phishingemails"),
        ]),
        ("EMAIL INTAKE", [
            ("imapclient", "IMAP protocol client to talk to Gmail."),
            ("pyzmail36", "Parses raw email messages (subject, sender, body)."),
            ("Gmail App Passwords", "Scoped, revocable credentials for safe automation."),
        ]),
        ("FRONTEND / DASHBOARD", [
            ("Streamlit", "Turns Python into an interactive web app — no JS required."),
            ("Custom CSS (this page)", "Hacker-terminal theme: JetBrains Mono, VT323, CRT scanlines."),
        ]),
        ("CONFIG & SECURITY", [
            ("python-dotenv", "Loads secrets from a local .env file."),
            (".gitignore", "Prevents secrets from ever being pushed to GitHub."),
            ("Streamlit Secrets", "Cloud-side secret store for live deployments."),
        ]),
        ("DEPLOYMENT", [
            ("GitHub", "Version control + source of truth."),
            ("Streamlit Community Cloud", "Free hosting tier for live demo."),
            ("requirements.txt", "Reproducible install on any machine."),
        ]),
    ]

    for header, items in sections:
        st.markdown(f"### `> {header.lower().replace(' ', '_')}`")
        for name, desc in items:
            st.markdown(f"""
            <div class="layer-card">
              <div class="layer-title">▸ {name}</div>
              <div class="layer-detail" style="color:#c7ffcd;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# PAGE 5 — ABOUT
# ============================================================
def page_about():
    brand_banner()
    st.markdown("## `> about`")

    st.markdown("""
<div class="layer-card">
  <div class="layer-title">▸ THE PLATFORM</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.95rem;">
    <b style="color:#00ff41;">Security Minds Pro</b> is the cybersecurity learning platform
    under which this project was built. This dashboard, <i>Phish Sentinel</i>, is a project
    developed as part of coursework on that platform.
  </div>
</div>

<div class="layer-card">
  <div class="layer-title">▸ STUDENT / DEVELOPER</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.95rem;">
    <b style="color:#00ff41;">Abrar Jahin</b> — student of Security Minds Pro, author and
    maintainer of this project.
  </div>
</div>

<div class="layer-card">
  <div class="layer-title">▸ SUBMITTED TO</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.95rem;">
    <b style="color:#00b14f;">Mashihoor Sir</b> — Founder of Security Minds Pro.
  </div>
</div>

<div class="layer-card">
  <div class="layer-title">▸ THE PROJECT</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.95rem;">
    A multi-layer phishing email detection system combining classical rule heuristics,
    a Large Language Model, and a trained machine learning classifier behind a single
    fused verdict. Built to demonstrate defense-in-depth for email security.
  </div>
</div>

<div class="layer-card">
  <div class="layer-title">▸ ML TRAINING DATA</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.95rem;">
    The machine learning model was trained on the <b>Phishing Email Detection</b> dataset
    by <i>Cyber Cop</i>, sourced from Kaggle:<br>
    <a href="https://www.kaggle.com/datasets/subhajournal/phishingemails"
       style="color:#00ff41;" target="_blank">
       kaggle.com/datasets/subhajournal/phishingemails</a>
  </div>
</div>

<div class="layer-card">
  <div class="layer-title">▸ MISSION</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.95rem;">
    Make phishing detection transparent and educational. Every verdict shows
    <i>why</i> — which rule fired, which AI reason was cited, which ML probability tipped it.
    Black-box security is bad security.
  </div>
</div>

<div class="layer-card">
  <div class="layer-title">▸ DESIGN PRINCIPLES</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.95rem;">
    1. Defense in depth — no single layer decides.<br>
    2. Explain every verdict — show the evidence, not just the score.<br>
    3. Fail safe — if a layer is unavailable, fall back gracefully.<br>
    4. Provider-agnostic AI — swap OpenAI / Gemini / Groq in one file.
  </div>
</div>

<div class="layer-card">
  <div class="layer-title">▸ ACADEMIC USE</div>
  <div class="layer-detail" style="color:#c7ffcd; font-size:0.95rem;">
    Educational coursework project. Do not feed real sensitive emails to free-tier hosted
    LLMs; inputs may be retained for model training unless you opt out at the provider level.
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# ROUTER
# ============================================================
if page.endswith("Scan Email"):
    page_scan()
elif page.endswith("Inbox Monitor"):
    page_inbox()
elif page.endswith("Learn the Project"):
    page_learn()
elif page.endswith("Tech Stack"):
    page_tech()
else:
    page_about()
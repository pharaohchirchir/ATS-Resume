"""
app.py — ATS Resume Studio (Modular Edition)
Entry point: run with `streamlit run app.py`

Folder structure:
    app.py
    config/
        settings.py          API key & model config (no .env needed)
    components/
        sidebar.py           Sidebar with API key input
        tab_analyze.py       Analyze tab
        tab_premium.py       Premium Solutions tab
    prompts/
        templates.py         All prompt strings
    utils/
        ai_client.py         Groq API wrapper
        docx_builder.py      DOCX export
        logger.py            CSV usage logging
        text_processing.py   PDF extraction, keyword match, sanitize
"""

import sys
import os

# Allow imports from the project root
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from components.sidebar import render_sidebar
from components.tab_analyze import render_tab_analyze
from components.tab_premium import render_tab_premium
from utils.logger import init_log_file

# ──────────────────────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ATS Resume Studio",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# Global CSS
# ──────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600;700&display=swap');

    /* ── Root variables ── */
    :root {
        --ink:        #0f1117;
        --ink-muted:  #4b5563;
        --accent:     #2563eb;
        --accent-lt:  #eff6ff;
        --success:    #16a34a;
        --warn:       #d97706;
        --danger:     #dc2626;
        --card-bg:    #ffffff;
        --page-bg:    #f1f5f9;
        --border:     #e2e8f0;
        --radius:     12px;
        --shadow:     0 2px 12px rgba(15,17,23,0.07);
    }

    /* ── Page background ── */
    .stApp {
        background: var(--page-bg);
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #0f1117 !important;
        border-right: 1px solid #1e2433;
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        background: #1e2433 !important;
        color: #e2e8f0 !important;
        border: 1px solid #2d3748 !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: #2d3748 !important;
    }
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] textarea {
        background: #1e2433 !important;
        border-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background: #1e2433 !important;
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h4 {
        color: #94a3b8 !important;
    }
    section[data-testid="stSidebar"] .stSlider .st-emotion-cache-1inwz65 {
        color: #e2e8f0 !important;
    }

    /* ── Main header ── */
    .studio-header {
        background: linear-gradient(135deg, #0f1117 0%, #1e3a5f 60%, #2563eb 100%);
        padding: 36px 40px;
        border-radius: var(--radius);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .studio-header::before {
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 260px; height: 260px;
        border-radius: 50%;
        background: rgba(37,99,235,0.18);
    }
    .studio-header::after {
        content: '';
        position: absolute;
        bottom: -80px; left: -40px;
        width: 200px; height: 200px;
        border-radius: 50%;
        background: rgba(37,99,235,0.10);
    }
    .studio-header h1 {
        font-family: 'DM Serif Display', serif;
        font-size: 36px;
        color: #ffffff;
        margin: 0 0 6px 0;
        position: relative;
        z-index: 1;
    }
    .studio-header p {
        font-size: 15px;
        color: #94a3b8;
        margin: 0;
        position: relative;
        z-index: 1;
    }
    .studio-header .badge-row {
        display: flex;
        gap: 8px;
        margin-top: 16px;
        position: relative;
        z-index: 1;
        flex-wrap: wrap;
    }
    .badge {
        background: rgba(255,255,255,0.12);
        color: #cbd5e1;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.15);
        backdrop-filter: blur(4px);
    }

    /* ── Tab bar ── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        gap: 4px;
        border-bottom: 2px solid var(--border);
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        font-size: 15px;
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        color: var(--ink-muted);
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent) !important;
        background: var(--card-bg) !important;
        border: 1px solid var(--border);
        border-bottom: 2px solid var(--card-bg);
        margin-bottom: -2px;
    }

    /* ── Cards / expanders ── */
    .stExpander {
        background: var(--card-bg);
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow);
        margin-bottom: 14px;
    }
    .stExpander summary {
        font-weight: 600 !important;
        font-size: 15px !important;
        color: var(--ink) !important;
        padding: 14px 16px !important;
    }

    /* ── Section labels ── */
    .section-label {
        font-family: 'DM Serif Display', serif;
        font-size: 22px;
        color: var(--ink);
        margin: 0 0 4px 0;
    }

    /* ── Buttons ── */
    .stButton button {
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        border-radius: 8px !important;
        transition: all 0.18s ease;
    }
    .stButton button[kind="primary"] {
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        color: #fff !important;
    }
    .stButton button[kind="primary"]:hover {
        background: #1d4ed8 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37,99,235,0.3);
    }
    .stButton button:not([kind="primary"]):hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        transform: translateY(-1px);
    }

    /* ── Inputs ── */
    .stTextArea textarea,
    .stTextInput input {
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        transition: border-color 0.18s;
    }
    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    }

    /* ── Metrics ── */
    [data-testid="metric-container"] {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 12px 16px;
    }

    /* ── Download buttons ── */
    .stDownloadButton button {
        font-weight: 600;
        border-radius: 8px !important;
        width: 100%;
    }

    /* ── Footer ── */
    .studio-footer {
        text-align: center;
        padding: 24px 0 12px 0;
        color: var(--ink-muted);
        font-size: 13px;
        border-top: 1px solid var(--border);
        margin-top: 32px;
    }

    /* ── Progress bar ── */
    .stProgress > div > div {
        background: linear-gradient(90deg, #2563eb, #06b6d4) !important;
        border-radius: 99px !important;
    }

    /* ── Info / warning / success boxes ── */
    .stAlert {
        border-radius: 10px !important;
    }

    /* ── Dividers ── */
    hr {
        border-color: var(--border) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        border-radius: 10px !important;
    }

    /* ── Form submit button ── */
    .stFormSubmitButton button {
        font-weight: 700;
        font-size: 15px;
        padding: 12px 24px;
        border-radius: 8px !important;
    }

    /* ── Selectbox ── */
    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: var(--accent) !important;
    }

    /* ── API key hint box ── */
    .api-hint {
        background: var(--accent-lt);
        border: 1px solid #bfdbfe;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 18px;
        font-size: 14px;
        color: #1e3a5f;
    }
    .api-hint strong { color: var(--accent); }

    /* mobile adjustments */
    @media (max-width: 768px) {
        .studio-header { padding: 20px; }
        .studio-header h1 { font-size: 24px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# Session state defaults
# ──────────────────────────────────────────────────────────────

DEFAULTS = {
    "jd": "",
    "resume": "",
    "inferred_field": "",
    "last_match": None,
    "last_analysis": "",
    "do_analysis": False,
    "do_quickfix": False,
    "usage_count": 0,
    "recent_usage": [],
    "premium_tools_output": {},
    "premium_resume_output": {},
    "premium_cover_output": {},
    "premium_custom_output": "",
    "ideal_resume": "",
    "key_reqs": "",
    "groq_api_key": "",
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────
# Init log file
# ──────────────────────────────────────────────────────────────

init_log_file()

# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────

prefs = render_sidebar()

# ──────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="studio-header">
        <h1>📄 ATS Resume Studio</h1>
        <p>Tailored resume analysis &amp; generation for any profession — Created by Pharaoh Chirchir</p>
        <div class="badge-row">
            <span class="badge">⚡ Instant ATS Scoring</span>
            <span class="badge">🧠 Expert AI Analysis</span>
            <span class="badge">✉️ Cover Letter Gen</span>
            <span class="badge">📥 DOCX Export</span>
            <span class="badge">🌐 Universal — Any Field</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# API key prompt banner (shown when key not set)
if not prefs["api_ready"]:
    st.markdown(
        """
        <div class="api-hint">
            🔑 <strong>Getting started:</strong> Enter your free Groq API key in the sidebar to unlock all AI features.
            Get one in seconds at <a href="https://console.groq.com" target="_blank">console.groq.com</a> — no credit card required.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────
# Main tabs
# ──────────────────────────────────────────────────────────────

tab_analyze, tab_premium, tab_help = st.tabs(
    ["🔍 Analyze", "💎 Premium Solutions", "❓ How It Works"]
)

with tab_analyze:
    render_tab_analyze(prefs)

with tab_premium:
    render_tab_premium(prefs)

with tab_help:
    st.markdown(
        """
        ## How to Use ATS Resume Studio

        ### Step 1 — Set your API Key
        Open the sidebar and paste your **Groq API key** (free at console.groq.com).
        Your key is stored in your browser session only and never saved to disk.

        ---

        ### Step 2 — Go to the Analyze tab
        - **Paste the Job Description** you're applying to.
        - **Upload your PDF resume** or paste it as text.
        - Hit **Quick Keyword Match** to see an instant ATS score with matched/missing keywords.
        - Hit **Run Expert Analysis** for a full AI-powered evaluation including strengths, weaknesses, rewrite suggestions, and your one-minute pitch.
        - Hit **Quick Fix Bullets** to generate bullet points that fill your keyword gaps.

        ---

        ### Step 3 — Generate Premium Outputs
        Switch to the **Premium Solutions** tab:

        | Feature | What it does |
        |---|---|
        | 📊 ATS Percentage Match | Weighted scoring matching real ATS algorithms |
        | 🎯 Recruiter Feedback | "Sarah Chen" gives brutally honest scored feedback |
        | 📄 Resume Generation | Full ATS-optimized resume built from yours + the JD |
        | ✉️ Cover Letter | Concise, tone-matched cover letter |
        | 💬 Custom Query | Ask any specific question about your fit |

        ---

        ### Tips for Best Results
        - Paste the **full** job description, not just the title.
        - Use your **complete** resume text for best tailoring.
        - Set a **Target Field** in the sidebar if the JD is short or generic.
        - Download the **DOCX** for a formatted, ATS-ready document.

        ---

        ### Privacy Note
        Your resume and job description are sent to **Groq's API** for AI processing.
        Nothing is stored permanently — all data lives in your browser session.
        """
    )

# ──────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="studio-footer">
        ATS Resume Studio · Groq-powered AI · 
        <a href="https://console.groq.com" target="_blank">Get your API key</a> · 
        All analysis stays in your session
    </div>
    """,
    unsafe_allow_html=True,
)

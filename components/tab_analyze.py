"""
components/tab_analyze.py — Analyze tab: JD + resume input, keyword match, expert analysis.
"""

import streamlit as st
from prompts.templates import EXPERT_ANALYSIS_PROMPT, PERCENTAGE_MATCH_PROMPT
from utils.ai_client import get_ai_response
from utils.logger import log_usage
from utils.text_processing import (
    compute_match_score,
    extract_text_from_pdf,
    format_resume_for_display,
    sanitize_display_text,
)
from config.settings import get_api_key, get_model, is_api_key_set


def _display_md(text: str, **kwargs):
    st.markdown(sanitize_display_text(text), **kwargs)


def _infer_field(jd_text: str, prefs: dict) -> str:
    """Infer field from JD or return the user-set field."""
    if prefs.get("target_field", "").strip():
        return prefs["target_field"].strip()
    if prefs.get("auto_infer_field") and jd_text.strip() and is_api_key_set():
        from prompts.templates import INFER_FIELD_PROMPT
        resp = get_ai_response(get_api_key(), get_model(), INFER_FIELD_PROMPT.format(jd=jd_text))
        label = resp.strip().splitlines()[0][:40].strip("\"' ")
        st.session_state["inferred_field"] = label
        return label or "General"
    return st.session_state.get("inferred_field", "General")


def render_tab_analyze(prefs: dict):
    """Render the Analyze tab."""

    # ── Input section ──────────────────────────────────────────────────────────
    st.markdown(
        '<p class="section-label">📋 Input — Job Description & Resume</p>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([3, 2], gap="large")

    with left:
        jd_raw = st.text_area(
            "Paste Job Description",
            height=230,
            key="jd_raw",
            placeholder="Paste the full job description here…",
            help="The AI will extract keywords and align your resume to this JD.",
        )

        # Sanitize
        jd = "" if ("{" in jd_raw and "}" in jd_raw and "background" in jd_raw.lower()) else jd_raw
        st.session_state["jd"] = jd

        uploaded = st.file_uploader(
            "Upload Resume (PDF)",
            type=["pdf"],
            key="upload_pdf",
            help="We'll extract the text automatically.",
        )
        extracted = ""
        if uploaded:
            with st.spinner("Extracting PDF text…"):
                extracted = extract_text_from_pdf(uploaded)
            if not extracted:
                st.warning("Could not extract text from this PDF — paste your resume below instead.")

        resume_raw = st.text_area(
            "Or Paste Resume Text",
            value=extracted,
            height=200,
            key="resume_raw",
            placeholder="Paste resume text here (or upload PDF above)…",
        )
        resume = resume_raw or extracted or ""
        st.session_state["resume"] = resume

    with right:
        st.markdown("#### 📊 Live Match Preview")
        jd_ok = bool(st.session_state.get("jd", "").strip())
        res_ok = bool(st.session_state.get("resume", "").strip())

        if jd_ok and res_ok:
            score, matched, missing = compute_match_score(
                st.session_state["jd"], st.session_state["resume"]
            )
            # Score gauge
            colour = "#22c55e" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
            st.markdown(
                f"""
                <div style="text-align:center; padding:16px; background:#f8faff;
                            border-radius:12px; border:1px solid #e0e8ff; margin-bottom:12px;">
                    <div style="font-size:52px; font-weight:800; color:{colour}; line-height:1;">
                        {score}%
                    </div>
                    <div style="font-size:13px; color:#666; margin-top:4px;">ATS Keyword Match</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(score / 100)

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Matched", f"{len(matched)} keywords")
            with col_b:
                st.metric("Missing", f"{len(missing)} keywords")

            with st.expander(f"✅ Matched ({len(matched)})"):
                st.write(", ".join(matched[:50]) or "—")
            with st.expander(f"❌ Missing ({len(missing)})"):
                st.write(", ".join(missing[:50]) or "—")
        else:
            st.info("Paste a Job Description **and** resume on the left to see your live match score.")

    st.divider()

    # ── Action buttons ─────────────────────────────────────────────────────────
    st.markdown("#### ⚡ Quick Actions")
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🔍 Quick Keyword Match", use_container_width=True):
            if not st.session_state.get("jd", "").strip() or not st.session_state.get("resume", "").strip():
                st.error("Provide both JD and resume first.")
            else:
                score, matched, missing = compute_match_score(
                    st.session_state["jd"], st.session_state["resume"]
                )
                st.success(f"Score: **{score}%** — {len(matched)} keywords matched, {len(missing)} missing.")
                st.session_state["last_match"] = (score, matched, missing)
                log_usage("quick_keyword_match", fields=prefs.get("target_field", ""))

    with c2:
        if st.button("🧠 Run Expert Analysis", use_container_width=True, type="primary"):
            if not prefs["api_ready"]:
                st.error("Enter your Groq API key in the sidebar first.")
            elif not st.session_state.get("jd", "").strip() or not st.session_state.get("resume", "").strip():
                st.error("Provide both JD and resume first.")
            else:
                st.session_state["do_analysis"] = True

    with c3:
        if st.button("⚡ Quick Fix Bullets", use_container_width=True):
            if not prefs["api_ready"]:
                st.error("Enter your Groq API key in the sidebar first.")
            elif not st.session_state.get("jd", "").strip() or not st.session_state.get("resume", "").strip():
                st.error("Provide both JD and resume first.")
            else:
                st.session_state["do_quickfix"] = True

    # ── Expert analysis ────────────────────────────────────────────────────────
    if st.session_state.get("do_analysis"):
        fields_str = _infer_field(st.session_state.get("jd", ""), prefs)
        prompt = EXPERT_ANALYSIS_PROMPT.format(
            fields=fields_str,
            jd=st.session_state.get("jd", ""),
            text=st.session_state.get("resume", ""),
        )
        with st.spinner("Running expert analysis…"):
            analysis = get_ai_response(get_api_key(), get_model(), prompt)

        st.markdown(f"### 🧠 Expert Analysis — *{fields_str}*")
        _display_md(analysis)
        st.session_state["last_analysis"] = analysis
        st.session_state["do_analysis"] = False
        log_usage("expert_analysis", fields=fields_str)

    # ── Quick fix bullets ──────────────────────────────────────────────────────
    if st.session_state.get("do_quickfix"):
        jd_v = st.session_state.get("jd", "")
        res_v = st.session_state.get("resume", "")
        _, _, missing = compute_match_score(jd_v, res_v) if jd_v and res_v else (0, [], [])
        top_missing = missing[:8]

        fields_q = prefs.get("target_field", "").strip() or st.session_state.get("inferred_field", "General")
        q_prompt = (
            f"You are a resume editor for {fields_q}. "
            f"Missing keywords: {top_missing}. "
            f"Write {prefs.get('achievements_count', 4)} sharp resume bullets "
            "(10-18 words each) with strong, quantified results."
        )
        with st.spinner("Generating bullets…"):
            fixes = get_ai_response(get_api_key(), get_model(), q_prompt)

        st.markdown("### ⚡ Quick Fix Bullets")
        _display_md(fixes)
        st.session_state["do_quickfix"] = False
        log_usage("quick_fix_bullets", fields=fields_q)

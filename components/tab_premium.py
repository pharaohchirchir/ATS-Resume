"""
components/tab_premium.py — Premium Solutions tab: resume gen, cover letter, recruiter feedback.
"""

import re

import streamlit as st

from config.settings import get_api_key, get_model, is_api_key_set
from prompts.templates import (
    ACHIEVEMENT_PROMPT,
    COVER_LETTER_PROMPT,
    CUSTOM_QUERY_PROMPT,
    IDEAL_RESUME_PROMPT,
    INFER_FIELD_PROMPT,
    PERCENTAGE_MATCH_PROMPT,
    RECRUITER_FEEDBACK_PROMPT,
)
from utils.ai_client import get_ai_response
from utils.docx_builder import make_docx_from_text
from utils.logger import log_usage
from utils.text_processing import (
    clean_resume_output,
    compute_match_score,
    format_resume_for_display,
    sanitize_display_text,
)


def _display_md(text: str, **kwargs):
    st.markdown(sanitize_display_text(text), **kwargs)


def _infer_field(jd_text: str, prefs: dict) -> str:
    if prefs.get("target_field", "").strip():
        return prefs["target_field"].strip()
    if prefs.get("auto_infer_field") and jd_text.strip() and is_api_key_set():
        resp = get_ai_response(
            get_api_key(), get_model(), INFER_FIELD_PROMPT.format(jd=jd_text)
        )
        label = resp.strip().splitlines()[0][:40].strip("\"' ")
        st.session_state["inferred_field"] = label
        return label or "General"
    return st.session_state.get("inferred_field", "General")


def _api_guard(prefs: dict) -> bool:
    if not prefs["api_ready"]:
        st.error("🔑 Enter your Groq API key in the sidebar to use this feature.")
        return False
    return True


def _jd_resume_guard() -> bool:
    if not st.session_state.get("jd", "").strip() or not st.session_state.get("resume", "").strip():
        st.error("📋 Provide both JD and resume in the **Analyze** tab first.")
        return False
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Main render
# ──────────────────────────────────────────────────────────────────────────────

def render_tab_premium(prefs: dict):
    """Render all premium solution sections."""

    st.markdown(
        '<p class="section-label">💎 Premium Solutions</p>',
        unsafe_allow_html=True,
    )
    st.caption("All actions use the JD & resume you provided in the Analyze tab.")

    # ── Section 1: Tools ──────────────────────────────────────────────────────
    with st.expander("🛠️ 1 · Tools & Quick Actions", expanded=True):
        _render_tools(prefs)

    # ── Section 2: Resume Generation ─────────────────────────────────────────
    with st.expander("📄 2 · Resume Generation", expanded=False):
        _render_resume_gen(prefs)

    # ── Section 3: Cover Letter ───────────────────────────────────────────────
    with st.expander("✉️ 3 · Cover Letter Generation", expanded=False):
        _render_cover_letter(prefs)

    # ── Section 4: Custom Query ───────────────────────────────────────────────
    with st.expander("💬 4 · Custom Query", expanded=False):
        _render_custom_query(prefs)


# ──────────────────────────────────────────────────────────────────────────────
# Section renderers
# ──────────────────────────────────────────────────────────────────────────────

def _render_tools(prefs: dict):
    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

    with col1:
        st.markdown("**📊 ATS Percentage Match**")
        st.caption("Premium ATS scoring with weighted keyword analysis.")
        if st.button("Run ATS Match", key="btn_pct_match", use_container_width=True):
            if _api_guard(prefs) and _jd_resume_guard():
                with st.spinner("Scoring…"):
                    result = get_ai_response(
                        get_api_key(),
                        get_model(),
                        PERCENTAGE_MATCH_PROMPT.format(
                            jd=st.session_state["jd"], text=st.session_state["resume"]
                        ),
                    )
                st.session_state.setdefault("premium_tools_output", {})["percentage_match"] = result
                log_usage("percentage_match", fields=prefs.get("target_field", ""))

    with col2:
        st.markdown("**🎯 Recruiter Feedback**")
        st.caption("Brutally honest mock recruiter review with a scored rubric.")
        if st.button("Get Recruiter Feedback", key="btn_recruiter", use_container_width=True):
            if _api_guard(prefs) and _jd_resume_guard():
                fields_ctx = _infer_field(st.session_state.get("jd", ""), prefs)
                with st.spinner("Sarah Chen is reviewing your resume… (30-60 s)"):
                    result = get_ai_response(
                        get_api_key(),
                        get_model(),
                        RECRUITER_FEEDBACK_PROMPT.format(
                            fields=fields_ctx,
                            jd=st.session_state["jd"],
                            resume=st.session_state["resume"],
                        ),
                        max_tokens=6000,
                    )
                st.session_state.setdefault("premium_tools_output", {})["recruiter_feedback"] = result
                log_usage("recruiter_feedback", fields=fields_ctx)

    with col3:
        st.markdown("**❓ Quick Tool Question**")
        st.caption("Ask anything about the JD vs resume.")
        quick_q = st.text_input("e.g. 'What are my top 3 gaps?'", key="tools_quick_q")
        if st.button("Ask", key="btn_tool_q", use_container_width=True):
            if _api_guard(prefs) and _jd_resume_guard():
                if not quick_q.strip():
                    st.error("Enter a question first.")
                else:
                    with st.spinner("Thinking…"):
                        result = get_ai_response(
                            get_api_key(),
                            get_model(),
                            CUSTOM_QUERY_PROMPT.format(
                                custom_query=quick_q,
                                jd=st.session_state["jd"],
                                text=st.session_state["resume"],
                            ),
                        )
                    st.session_state.setdefault("premium_tools_output", {})["tool_query"] = result
                    log_usage("tool_query")

    # Display tool results
    tool_out = st.session_state.get("premium_tools_output", {})
    if tool_out:
        st.divider()
        if "percentage_match" in tool_out:
            st.markdown("##### 📊 ATS Match Result")
            _display_md(tool_out["percentage_match"])
            st.divider()
        if "recruiter_feedback" in tool_out:
            st.markdown("##### 🎯 Recruiter Feedback")
            _display_md(tool_out["recruiter_feedback"])
            st.divider()
        if "tool_query" in tool_out:
            st.markdown("##### 💬 Query Answer")
            _display_md(tool_out["tool_query"])


def _render_resume_gen(prefs: dict):
    jd_ok = bool(st.session_state.get("jd", "").strip())
    res_ok = bool(st.session_state.get("resume", "").strip())

    if not jd_ok:
        st.info("Paste the Job Description in the Analyze tab first.")
    if res_ok:
        st.success("✅ Will use your resume as foundation.")
    else:
        st.warning("No resume found — a template will be generated. Add your resume in Analyze for best results.")

    with st.form("resume_gen_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            job_title_input = st.text_input("Target Job Title (optional)", key="rg_job_title")
        with col_b:
            bullets_count = st.select_slider(
                "Bullets per role", [3, 4, 5, 6, 7], value=prefs["achievements_count"]
            )
        include_phone = st.checkbox("Keep contact placeholders if missing", value=True)
        submitted = st.form_submit_button("✨ Generate ATS-Optimized Resume", type="primary", use_container_width=True)

    if submitted:
        if not _api_guard(prefs):
            return
        if not jd_ok:
            st.error("Paste the JD first.")
            return

        fields_str = _infer_field(st.session_state.get("jd", ""), prefs)
        job_title = job_title_input.strip() or get_ai_response(
            get_api_key(),
            get_model(),
            f"What is the most likely job title for this JD? Reply with title only.\n\n{st.session_state['jd']}",
        ).strip() or "Target Role"

        user_resume = st.session_state.get("resume", "").strip()

        with st.spinner("Generating achievements…"):
            ach_prompt = ACHIEVEMENT_PROMPT.format(
                job_title=job_title,
                key_requirements=st.session_state.get("key_reqs", ""),
                count=bullets_count,
            )
            achievements = clean_resume_output(get_ai_response(get_api_key(), get_model(), ach_prompt))

        with st.spinner("Building ATS-optimized resume…"):
            base = IDEAL_RESUME_PROMPT.format(fields=fields_str, jd=st.session_state["jd"])
            if user_resume:
                resume_prompt = (
                    base
                    + f"\n\n**User's Current Resume (USE AS FOUNDATION):**\n{user_resume}\n\n"
                    "**Transform the above resume: preserve all real experience and achievements "
                    "while fully optimizing for the target JD.**"
                )
            else:
                resume_prompt = (
                    base
                    + "\n\n**No existing resume provided. Create a strong template structure.**"
                )
            ideal_resume = clean_resume_output(get_ai_response(get_api_key(), get_model(), resume_prompt))

        if not include_phone:
            for ph in [r"\[Your Phone Number\]", r"\[Your Email\]", r"\[LinkedIn Profile URL\]", r"\[City, State/Country\]"]:
                ideal_resume = re.sub(ph, "", ideal_resume, flags=re.IGNORECASE)
            ideal_resume = re.sub(r"\s*\|\s*\|\s*", " | ", ideal_resume)
            ideal_resume = re.sub(r"^\s*\|\s*$", "", ideal_resume, flags=re.MULTILINE)

        st.session_state["premium_resume_output"] = {
            "job_title": job_title,
            "fields": fields_str,
            "achievements": achievements,
            "resume": ideal_resume,
            "used_resume": bool(user_resume),
        }
        st.session_state["ideal_resume"] = ideal_resume
        log_usage("generate_resume", fields=fields_str, job_title=job_title)

    # Show results
    rout = st.session_state.get("premium_resume_output", {})
    if rout:
        st.divider()
        badge = "✅ Built from your resume + JD" if rout.get("used_resume") else "⚠️ Template (no resume provided)"
        st.info(f"{badge}  |  **Role:** {rout.get('job_title')}  |  **Field:** {rout.get('fields')}")

        tabs = st.tabs(["📄 Resume Preview", "💡 Achievement Examples"])
        with tabs[0]:
            formatted = format_resume_for_display(rout.get("resume", ""))
            st.markdown(
                '<div style="background:white; padding:28px 32px; border-radius:10px; '
                'border:1px solid #e0e0e0; font-family:Georgia,serif; line-height:1.7;">',
                unsafe_allow_html=True,
            )
            st.markdown(formatted)
            st.markdown("</div>", unsafe_allow_html=True)

        with tabs[1]:
            _display_md(rout.get("achievements", ""))

        # Downloads
        dl1, dl2 = st.columns(2)
        with dl1:
            docx_bytes = make_docx_from_text(rout.get("resume", ""), name=rout.get("job_title", ""))
            st.download_button(
                "📥 Download DOCX",
                data=docx_bytes,
                file_name="ATS_Optimized_Resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                "📥 Download Markdown",
                data=rout.get("resume", "").encode(),
                file_name="ats_optimized_resume.md",
                mime="text/markdown",
                use_container_width=True,
            )

        # Comparison — use a toggle button instead of a nested expander
        if rout.get("used_resume"):
            st.divider()
            if st.button(
                "🔄 Toggle Side-by-Side Comparison",
                key="toggle_comparison",
                use_container_width=True,
            ):
                st.session_state["show_comparison"] = not st.session_state.get("show_comparison", False)

            if st.session_state.get("show_comparison", False):
                with st.container():
                    st.markdown("#### 🔄 Original vs Optimized")
                    cc1, cc2 = st.columns(2, gap="large")
                    orig = st.session_state.get("resume", "")
                    opt = rout.get("resume", "")
                    jd_text = st.session_state.get("jd", "")

                    with cc1:
                        st.markdown("**📄 Original**")
                        st.caption(f"{len(orig.split())} words · {len(orig.splitlines())} lines")
                        st.text_area("orig", value=orig, height=420, disabled=True, label_visibility="collapsed")
                    with cc2:
                        st.markdown("**✨ Optimized**")
                        st.caption(f"{len(opt.split())} words · {len(opt.splitlines())} lines")
                        st.text_area("opt", value=opt, height=420, disabled=True, label_visibility="collapsed")

                    if jd_text:
                        m1, m2, m3 = st.columns(3)
                        os_, _, _ = compute_match_score(jd_text, orig)
                        ots, _, _ = compute_match_score(jd_text, opt)
                        with m1:
                            st.metric("ATS Score", f"{ots}%", delta=f"+{ots-os_}%")
                        with m2:
                            st.metric("Words", len(opt.split()), delta=len(opt.split()) - len(orig.split()))
                        with m3:
                            orig_b = orig.count("•") + len(re.findall(r"^\s*[-\*]\s", orig, re.M))
                            opt_b = opt.count("•") + len(re.findall(r"^\s*[-\*]\s", opt, re.M))
                            st.metric("Bullets", opt_b, delta=opt_b - orig_b)


def _render_cover_letter(prefs: dict):
    with st.form("cover_gen_form"):
        tone = st.selectbox(
            "Tone",
            ["Confident & Direct", "Warm & Collaborative", "Humble & Impact-Focused"],
            key="cg_tone",
        )
        snippet = st.text_area(
            "Short Resume Snippet (optional — 1-3 lines)",
            height=80,
            key="cg_snip",
            placeholder="e.g. 5 years in digital marketing, led campaigns generating $2M in pipeline…",
        )
        submitted = st.form_submit_button("✉️ Generate Cover Letter", type="primary", use_container_width=True)

    if submitted:
        if not _api_guard(prefs):
            return
        if not st.session_state.get("jd", "").strip():
            st.error("Paste the JD in the Analyze tab first.")
            return

        snippet_use = snippet.strip() or st.session_state.get("resume", "")[:500] or "Experienced professional."
        with st.spinner("Writing cover letter…"):
            letter = get_ai_response(
                get_api_key(),
                get_model(),
                COVER_LETTER_PROMPT.format(
                    tone=tone, jd=st.session_state["jd"], resume_snippet=snippet_use
                ),
            )
        st.session_state["premium_cover_output"] = {"tone": tone, "letter": letter}
        log_usage("generate_cover_letter")

    cov = st.session_state.get("premium_cover_output", {})
    if cov:
        st.divider()
        st.markdown(f"*Tone: {cov.get('tone')}*")
        _display_md(cov.get("letter", ""))

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "📥 Download DOCX",
                data=make_docx_from_text(cov.get("letter", "")),
                file_name="Cover_Letter.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                "📥 Download Markdown",
                data=cov.get("letter", "").encode(),
                file_name="cover_letter.md",
                mime="text/markdown",
                use_container_width=True,
            )


def _render_custom_query(prefs: dict):
    custom_q = st.text_input(
        "Your question",
        key="premium_custom_q",
        placeholder="e.g. What are my top 3 gaps? / How should I tailor my summary?",
    )
    if st.button("💬 Ask", key="btn_custom_q", type="primary", use_container_width=True):
        if not _api_guard(prefs):
            return
        if not _jd_resume_guard():
            return
        if not custom_q.strip():
            st.error("Enter a question first.")
            return
        with st.spinner("Thinking…"):
            answer = get_ai_response(
                get_api_key(),
                get_model(),
                CUSTOM_QUERY_PROMPT.format(
                    custom_query=custom_q,
                    jd=st.session_state["jd"],
                    text=st.session_state["resume"],
                ),
            )
        st.session_state["premium_custom_output"] = answer
        log_usage("custom_query")

    if st.session_state.get("premium_custom_output"):
        st.divider()
        _display_md(st.session_state["premium_custom_output"])

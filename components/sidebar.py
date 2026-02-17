"""
components/sidebar.py — Sidebar with API key entry and preferences.
"""

import streamlit as st
from config.settings import (
    AVAILABLE_MODELS,
    GROQ_MODEL_DEFAULT,
    is_api_key_set,
    set_api_key,
)


def render_sidebar() -> dict:
    """
    Render the sidebar and return a dict of user preferences.

    Returns:
        {
            "target_field": str,
            "auto_infer_field": bool,
            "tone_choice": str,
            "humanize_level": int,
            "achievements_count": int,
            "api_ready": bool,
        }
    """
    with st.sidebar:
        # ── Brand ──────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center; padding: 12px 0 8px 0;">
                <span style="font-size:28px;">📄</span>
                <h2 style="margin:4px 0 2px 0; color:#1a1a2e; font-size:20px; font-weight:700;">
                    ATS Resume Studio
                </h2>
                <p style="margin:0; font-size:12px; color:#666;">Groq-powered · Universal</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # ── API Key ────────────────────────────────────────────
        st.markdown("#### 🔑 Groq API Key")

        api_key_input = st.text_input(
            "Enter your Groq API key",
            type="password",
            value=st.session_state.get("groq_api_key", ""),
            placeholder="gsk_...",
            help=(
                "Get a free key at console.groq.com. "
                "Your key is stored only in this browser session and never saved."
            ),
            key="api_key_input_field",
        )

        if api_key_input:
            set_api_key(api_key_input)

        if is_api_key_set():
            st.success("✅ API key set", icon="✅")
        else:
            st.warning("⚠️ Enter your Groq key to enable AI features", icon="⚠️")
            st.markdown(
                "[Get a free key →](https://console.groq.com)",
                unsafe_allow_html=False,
            )

        # ── Model ──────────────────────────────────────────────
        st.markdown("#### 🤖 Model")
        model = st.selectbox(
            "Groq model",
            AVAILABLE_MODELS,
            index=0,
            key="groq_model",
            help="llama-3.3-70b-versatile is fast and high quality.",
        )

        st.divider()

        # ── Preferences ────────────────────────────────────────
        st.markdown("#### ⚙️ Preferences")

        target_field = st.text_input(
            "Target field / industry",
            placeholder="e.g. Marketing, Healthcare, DevOps",
            help="Leave blank to auto-infer from the Job Description.",
            key="target_field_input",
        )

        auto_infer = st.checkbox(
            "Auto-infer field from JD",
            value=True,
            key="auto_infer_field",
            help="If checked and Target field is empty, AI infers the field from the JD.",
        )

        tone = st.selectbox(
            "Cover letter tone",
            ["Confident & Direct", "Warm & Collaborative", "Humble & Impact-Focused"],
            key="tone_choice",
        )

        achievements_count = st.slider(
            "Achievements per role",
            min_value=3,
            max_value=7,
            value=4,
            key="achievements_count",
        )

        st.divider()

        # ── Session stats ──────────────────────────────────────
        st.markdown("#### 📊 Session Stats")
        usage = st.session_state.get("usage_count", 0)
        last_action = st.session_state.get("last_action", "—")
        st.metric("Actions this session", usage)
        st.caption(f"Last: {last_action}")

        if st.button("🔄 Reset everything", use_container_width=True):
            for k in list(st.session_state.keys()):
                st.session_state.pop(k, None)
            st.rerun()

    return {
        "target_field": target_field,
        "auto_infer_field": auto_infer,
        "tone_choice": tone,
        "achievements_count": achievements_count,
        "api_ready": is_api_key_set(),
        "model": model,
    }

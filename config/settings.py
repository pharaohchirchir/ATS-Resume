"""
config/settings.py — API key and model configuration.
Keys are entered via the Streamlit UI and stored in session state only.
"""

import streamlit as st

GROQ_MODEL_DEFAULT = "llama-3.3-70b-versatile"

AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
]

def get_api_key() -> str:
    """Retrieve the Groq API key from session state."""
    return st.session_state.get("groq_api_key", "")

def set_api_key(key: str):
    """Store the API key in session state."""
    st.session_state["groq_api_key"] = key.strip()

def is_api_key_set() -> bool:
    """Check if a valid-looking API key has been set."""
    key = get_api_key()
    return bool(key and key.startswith("gsk_") and len(key) > 20)

def get_model() -> str:
    """Get the selected model from session state."""
    return st.session_state.get("groq_model", GROQ_MODEL_DEFAULT)

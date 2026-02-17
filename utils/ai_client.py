"""
utils/ai_client.py — Groq AI client wrapper.
API key is passed from session state (entered via UI).
"""

from groq import Groq


def get_ai_response(api_key: str, model: str, prompt: str, max_tokens: int = 4096) -> str:
    """
    Send a prompt to Groq and return the response text.

    Args:
        api_key:    Groq API key (entered by user in the sidebar).
        model:      Model name string (e.g. 'llama-3.3-70b-versatile').
        prompt:     The full prompt string.
        max_tokens: Maximum tokens for the response.

    Returns:
        Response text string, or an error message prefixed with '[AI Error]'.
    """
    if not api_key:
        return "[AI Error] No API key provided. Enter your Groq API key in the sidebar."

    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content or ""
    except Exception as exc:
        err = str(exc)
        if "401" in err or "invalid_api_key" in err.lower():
            return "[AI Error] Invalid API key. Please check the key you entered."
        if "429" in err:
            return "[AI Error] Rate limit hit. Please wait a moment and try again."
        return f"[AI Error] {err}"

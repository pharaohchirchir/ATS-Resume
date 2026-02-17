"""
utils/text_processing.py — PDF extraction, keyword matching, and text sanitization.
"""

import re
from collections import Counter

import PyPDF2 as pdf


# ──────────────────────────────────────────────────────────────
# PDF Extraction
# ──────────────────────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file) -> str:
    """Extract plain text from an uploaded PDF file object."""
    try:
        reader = pdf.PdfReader(uploaded_file)
        parts = []
        for page in reader.pages:
            try:
                txt = page.extract_text()
            except Exception:
                txt = ""
            if txt:
                parts.append(txt)
        return "\n".join(parts)
    except Exception:
        return ""


# ──────────────────────────────────────────────────────────────
# ATS Keyword Matching
# ──────────────────────────────────────────────────────────────

STOPWORDS = {
    "and", "or", "the", "a", "an", "to", "with", "of", "for", "in", "on",
    "by", "that", "is", "are", "as", "at", "from", "be", "using",
    "experience", "years", "year", "able", "work", "working", "ability",
}


def extract_keyword_set(text: str, min_len: int = 3) -> set:
    """Extract a deduplicated keyword set from text, removing stopwords."""
    if not text:
        return set()
    words = re.findall(r"[A-Za-z\+\#\.\-]{%d,}" % min_len, text.lower())
    return {w for w in words if w not in STOPWORDS}


def compute_match_score(jd_text: str, resume_text: str):
    """
    Compute a weighted ATS keyword match score.

    Returns:
        (score: int, matched: list[str], missing: list[str])
    """
    jd_kw = extract_keyword_set(jd_text)
    resume_kw = extract_keyword_set(resume_text)

    if not jd_kw:
        return 0, [], []

    matched = sorted(k for k in jd_kw if k in resume_kw)
    missing = sorted(k for k in jd_kw if k not in resume_kw)

    jd_counts = Counter(re.findall(r"[A-Za-z\+\#\.\-]{3,}", jd_text.lower()))
    total_weight = sum(jd_counts.get(k, 1) for k in jd_kw) or 1
    matched_weight = sum(jd_counts.get(k, 0) for k in matched)

    score = int((matched_weight / total_weight) * 100)
    return score, matched, missing


# ──────────────────────────────────────────────────────────────
# Text Sanitization & Cleaning
# ──────────────────────────────────────────────────────────────

def sanitize_display_text(text: str, placeholder: str = "[Removed]") -> str:
    """Basic sanitization to prevent injection in displayed output."""
    if not text:
        return ""
    if len(text) > 25_000:
        return f"{placeholder} — output too large to display safely."
    lowered = text.lower()
    if "{" in lowered and "}" in lowered and "background" in lowered:
        return f"{placeholder} — removed suspicious styling content."
    return text


def clean_resume_output(text: str) -> str:
    """Strip markdown formatting symbols from AI-generated resume text."""
    if not text:
        return ""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"^_{2,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-\*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_resume_for_display(text: str) -> str:
    """Convert plain resume text into markdown suitable for st.markdown display."""
    if not text:
        return ""

    lines = text.split("\n")
    out = []
    in_core_skills = False

    for line in lines:
        line = line.strip()

        if not line:
            if out and out[-1] != "":
                out.append("")
            continue

        # Section headers
        if (line.isupper() and len(line.split()) <= 4) or re.match(
            r"^(PROFESSIONAL SUMMARY|PROFESSIONAL EXPERIENCE|CORE SKILLS|"
            r"WORK EXPERIENCE|EDUCATION|CERTIFICATIONS?|TECHNICAL SKILLS|PROJECTS)[\s:]*$",
            line,
            re.I,
        ):
            in_core_skills = bool(
                re.match(r"^(CORE SKILLS|TECHNICAL SKILLS)[\s:]*$", line, re.I)
            )
            if out:
                out.extend(["", "---", ""])
            header = re.sub(r"[#\*_\-]{2,}", "", line.strip().rstrip(":")).strip()
            out.extend([f"### {header}", ""])
            continue

        # Skill category lines (bold label)
        if (
            ("–" in line or "—" in line or (":" in line and len(line.split(":")[0].split()) <= 6))
            and not line.startswith("[")
            and "|" not in line
        ):
            if "–" in line:
                parts = line.split("–", 1)
                formatted = f"**{parts[0].strip()}** – {parts[1].strip()}" if len(parts) > 1 else line
            elif "—" in line:
                parts = line.split("—", 1)
                formatted = f"**{parts[0].strip()}** — {parts[1].strip()}" if len(parts) > 1 else line
            elif ":" in line:
                parts = line.split(":", 1)
                formatted = f"**{parts[0].strip()}**: {parts[1].strip()}" if len(parts) > 1 else line
            else:
                formatted = line
            out.append(formatted)
            continue

        # Job title lines (pipe-separated)
        if "|" in line and not line.startswith("["):
            out.extend([f"**{line}**", ""])
            continue

        # Bullet points
        if not in_core_skills and (line.startswith("•") or line.startswith("-") or line.startswith("*")):
            bullet = re.sub(r"^[\•\-\*]\s+", "", line).strip()
            out.append(f"• {bullet}")
            continue

        # Contact info
        if any(kw in line.lower() for kw in ["@", "phone", "email", "linkedin", "github"]):
            out.extend([f"*{line}*", ""])
            continue

        out.append(line)

    return "\n".join(out)

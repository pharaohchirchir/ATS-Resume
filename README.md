# ATS Resume Studio

An ATS-powered resume analyzer and optimizer built with Streamlit and Groq AI.
Enter your Groq API key directly in the sidebar — **no `.env` file needed**.

## Folder Structure

```
ats_resume_studio/
├── app.py                    ← Entry point (run this)
├── requirements.txt
├── config/
│   └── settings.py           ← API key & model config (session-based)
├── components/
│   ├── sidebar.py            ← Sidebar with API key input
│   ├── tab_analyze.py        ← Analyze tab
│   └── tab_premium.py        ← Premium Solutions tab
├── prompts/
│   └── templates.py          ← All AI prompt templates
└── utils/
    ├── ai_client.py          ← Groq API wrapper
    ├── docx_builder.py       ← DOCX export
    ├── logger.py             ← CSV usage logging
    └── text_processing.py    ← PDF extract, keyword match, sanitize
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

## Getting a Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free) and create an API key
3. Paste the key (`gsk_...`) into the **sidebar** of the app

Your key is stored only in the browser session — never saved to disk.

## Features

| Feature | Description |
|---|---|
| 🔍 Instant ATS Score | Keyword-weighted match score vs job description |
| 🧠 Expert Analysis | AI strengths, weaknesses, rewrites, one-minute pitch |
| ⚡ Quick Fix Bullets | Auto-generated bullets to fill keyword gaps |
| 📊 ATS % Match (Premium) | Weighted scoring like real ATS systems |
| 🎯 Recruiter Feedback | Scored mock recruiter review with rubric |
| 📄 Resume Generation | Full ATS-optimized resume from your existing one |
| ✉️ Cover Letter | Tone-matched cover letter |
| 💬 Custom Query | Ask anything about your resume vs the JD |
| 📥 DOCX Export | Formatted Word document download |

## Supported Groq Models

- `llama-3.3-70b-versatile` (default, recommended)
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`

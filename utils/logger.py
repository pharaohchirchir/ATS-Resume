"""
utils/logger.py — Session-based usage logging (CSV + session state).
"""

import csv
import os
from datetime import datetime

import streamlit as st

LOG_FILE = "usage_logs.csv"


def init_log_file():
    """Create the CSV log file with headers if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp_utc", "action", "fields", "job_title", "status"])
        except Exception:
            pass


def log_usage(action: str, fields: str = "", job_title: str = "", status: str = "ok"):
    """Append a usage row to the CSV and update session state counters."""
    ts = datetime.utcnow().isoformat()
    try:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([ts, action, fields, job_title, status])
    except Exception:
        pass

    st.session_state["usage_count"] = st.session_state.get("usage_count", 0) + 1
    st.session_state["last_action"] = action
    logs = st.session_state.get("recent_usage", [])
    logs.insert(0, (ts, action, fields, job_title, status))
    st.session_state["recent_usage"] = logs[:50]

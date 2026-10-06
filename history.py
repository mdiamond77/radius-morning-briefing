"""
history.py
Read/write helper for history.json — a rolling 30-day per-center log of
daily session stats used to render the 7-day trend block in the email.
"""

import json
import os
from datetime import date

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "history.json")
MAX_DAYS = 30


def load_history() -> dict:
    if not os.path.exists(HISTORY_PATH):
        return {}
    with open(HISTORY_PATH) as f:
        return json.load(f)


def append_entry(center: str, report_date: date, total_sessions: int,
                 total_pages: int, avg_score) -> None:
    """Add or overwrite today's entry for this center and trim to MAX_DAYS."""
    history = load_history()
    entries = history.get(center, [])

    date_str = report_date.isoformat()
    avg_pages = round(total_pages / total_sessions, 1) if total_sessions else 0

    # Replace existing entry for this date if present
    entries = [e for e in entries if e["date"] != date_str]
    entries.append({
        "date":     date_str,
        "sessions": total_sessions,
        "avg_pages": avg_pages,
        "avg_score": avg_score,
    })

    entries.sort(key=lambda x: x["date"])
    history[center] = entries[-MAX_DAYS:]

    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)
    print(f"[history] Saved entry for {center} on {date_str}: "
          f"{total_sessions} sessions, {avg_pages} avg pages")


def get_recent(center: str, days: int = 7) -> list[dict]:
    """Return the last `days` entries for this center, newest first."""
    history = load_history()
    entries = history.get(center, [])
    return list(reversed(entries[-days:]))

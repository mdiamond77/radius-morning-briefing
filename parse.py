"""
parse.py
Reads the Radius CSV export and computes all stats needed for the report.
Returns a structured dict that generate.py and send.py consume.
"""

import csv
import re
from collections import defaultdict
from datetime import date, datetime


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def to_minutes(time_str: str) -> int | None:
    """Convert '4:35 PM' → minutes since midnight."""
    if not time_str or not str(time_str).strip():
        return None
    try:
        t = str(time_str).strip()
        parts = t.split(" ")
        h, m = map(int, parts[0].split(":"))
        if len(parts) > 1 and parts[1].upper() == "PM" and h != 12:
            h += 12
        if len(parts) > 1 and parts[1].upper() == "AM" and h == 12:
            h = 0
        return h * 60 + m
    except Exception:
        return None


def fmt_time(minutes: int) -> str:
    """Convert minutes since midnight → '4:30 PM'."""
    h = minutes // 60
    m = minutes % 60
    ampm = "PM" if h >= 12 else "AM"
    h12 = h - 12 if h > 12 else (12 if h == 0 else h)
    return f"{h12}:{m:02d} {ampm}"


def parse_lp(lp_str: str) -> tuple[list[str], list[str]]:
    """
    Parse LP Assignment column into (mastered_topics, worked_on_topics).
    Format: "CODE (Topic Name): Mastered;  CODE (Topic Name): Worked On; ..."
    """
    if not lp_str:
        return [], []
    mastered, worked = [], []
    for entry in lp_str.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        # Extract topic name from parentheses
        match = re.search(r'\(([^)]+)\)', entry)
        topic = match.group(1).strip() if match else entry
        if "Mastered" in entry:
            mastered.append(topic)
        elif "Worked On" in entry:
            worked.append(topic)
    return mastered, worked


def half_hour_buckets(sessions: list[dict]) -> list[dict]:
    """
    Build half-hour seat occupancy buckets from session start/end times.
    Returns list of {label, start_label, end_label, count, students, peak}.
    """
    # Find earliest start and latest end across all sessions
    all_starts = [s["start_min"] for s in sessions if s["start_min"]]
    all_ends   = [s["end_min"]   for s in sessions if s["end_min"]]
    if not all_starts:
        return []

    # Round down to nearest half hour
    earliest = (min(all_starts) // 30) * 30
    latest   = ((max(all_ends) + 29) // 30) * 30

    buckets = []
    for bucket_start in range(earliest, latest, 30):
        bucket_end = bucket_start + 30
        students_in_bucket = [
            s["name"] for s in sessions
            if s["start_min"] and s["end_min"]
            and s["start_min"] < bucket_end
            and s["end_min"] > bucket_start
        ]
        if students_in_bucket:
            buckets.append({
                "label":       f"{fmt_time(bucket_start)} \u2013 {fmt_time(bucket_end)}",
                "start_label": fmt_time(bucket_start),
                "end_label":   fmt_time(bucket_end),
                "count":       len(students_in_bucket),
                "students":    students_in_bucket,
                "peak":        False,
            })

    # Mark peak bucket
    if buckets:
        max_count = max(b["count"] for b in buckets)
        for b in buckets:
            if b["count"] == max_count:
                b["peak"] = True
                break

    return buckets


# ─── MAIN PARSE FUNCTION ──────────────────────────────────────────────────────

def parse_report(csv_path: str, report_date: date = None) -> dict:
    """
    Parse the Radius CSV export and return a structured data dict.
    """
    if report_date is None:
        report_date = date.today()

    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        return {}

    # ── Per-student session data ───────────────────────────────────────────────
    sessions = []
    for row in rows:
        mastered, worked_on = parse_lp(row.get("LP Assignment", ""))
        start_min = to_minutes(row.get("Session Start", ""))
        end_min   = to_minutes(row.get("Session End", ""))

        try:
            pages = int(row.get("Pages Completed") or 0)
        except ValueError:
            pages = 0

        try:
            goal = int(row.get("Session Page Goal") or 0)
        except ValueError:
            goal = 0

        try:
            score_raw = row.get("Mathlete Score", "").strip()
            score = float(score_raw) if score_raw else None
        except ValueError:
            score = None

        sessions.append({
            "name":           row.get("Student Name", "").strip(),
            "instructor":     row.get("Instructors", "").strip(),
            "start":          row.get("Session Start", "").strip(),
            "end":            row.get("Session End", "").strip(),
            "start_min":      start_min,
            "end_min":        end_min,
            "pages":          pages,
            "goal":           goal,
            "beat_goal":      pages > goal if goal else False,
            "score":          score,
            "mastered":       mastered,
            "worked_on":      worked_on,
            "session_notes":  (row.get("Session Summary Notes") or "").strip(),
            "internal_notes": (row.get("Internal Notes") or "").strip(),
            "lp_assigned":    bool((row.get("LP Assignment") or "").strip()),
            "delivery":       row.get("Delivery Method", "").strip(),
            "center":         row.get("Center", "").strip(),
        })

    # ── Aggregate stats ────────────────────────────────────────────────────────
    total_sessions  = len(sessions)
    unique_students = len(set(s["name"] for s in sessions))
    total_pages     = sum(s["pages"] for s in sessions)

    scores = [s["score"] for s in sessions if s["score"] is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # Mastery
    mastery_list = []
    for s in sessions:
        if s["mastered"]:
            mastery_list.append({"name": s["name"], "topics": s["mastered"]})
    total_mastery = sum(len(m["topics"]) for m in mastery_list)

    # Instructor breakdown
    instructor_map = defaultdict(list)
    team_taught    = set()
    for s in sessions:
        instructors = [i.strip() for i in s["instructor"].split(",") if i.strip()]
        for inst in instructors:
            instructor_map[inst].append(s["name"])
        if len(instructors) > 1:
            team_taught.add(s["name"])

    # Format instructor summary
    instructor_summary = []
    for inst, students in sorted(instructor_map.items(), key=lambda x: -len(x[1])):
        solo   = [st for st in students if st not in team_taught]
        teamed = [st for st in students if st in team_taught]
        note_parts = []
        if solo:
            note_parts.append(f"{len(solo)} solo")
        if teamed:
            note_parts.append(f"{len(teamed)} team-taught")
        instructor_summary.append({
            "name":     inst,
            "count":    len(students),
            "students": students,
            "detail":   ", ".join(note_parts) if note_parts else "",
        })

    # Attendance buckets (half-hour)
    att_buckets = half_hour_buckets(sessions)

    # Internal notes (instructor-written only)
    internal_notes = [
        {"name": s["name"], "note": s["internal_notes"]}
        for s in sessions
        if s["internal_notes"]
    ]

    # Missing LP
    missing_lp = [s["name"] for s in sessions if not s["lp_assigned"]]

    # Page goal performance
    beat_goal  = [s["name"] for s in sessions if s["beat_goal"]]
    below_goal = [
        f"{s['name']} ({s['pages']}/{s['goal']} pages)"
        for s in sessions
        if not s["beat_goal"] and s["goal"] > 0
    ]

    return {
        "report_date":       report_date.strftime("%A, %B %-d, %Y"),
        "center":            sessions[0]["center"].split(",")[0].strip() if sessions else "Center",
        "total_sessions":    total_sessions,
        "unique_students":   unique_students,
        "total_pages":       total_pages,
        "avg_score":         avg_score,
        "total_mastery":     total_mastery,
        "mastery_list":      mastery_list,
        "instructor_summary": instructor_summary,
        "att_buckets":       att_buckets,
        "internal_notes":    internal_notes,
        "missing_lp":        missing_lp,
        "beat_goal":         beat_goal,
        "below_goal":        below_goal,
        "sessions":          sessions,
    }


if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "downloads/radius_today.csv"
    data = parse_report(path)
    print(json.dumps(data, indent=2, default=str))

"""
generate.py
Calls the Claude API to generate the three AI-powered sections of the report:
  1. Executive Summary
  2. Standout Sessions
  3. Session Quality flags
"""

import os
import re
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL  = "claude-haiku-4-5-20251001"   # fast & cost-effective for nightly reports


# ─── EXECUTIVE SUMMARY ────────────────────────────────────────────────────────

def generate_executive_summary(data: dict) -> str:
    beat       = ", ".join(data["beat_goal"]) or "none"
    below      = ", ".join(data["below_goal"]) or "none"
    instructors = ", ".join(
        f"{i['name']} ({i['count']} students)"
        for i in data["instructor_summary"]
        if not i.get("is_center_director")
    )
    flags      = len(data["internal_notes"])
    missing_lp = len(data["missing_lp"])
    below_30   = [s for s in data["sessions"] if s["score"] is not None and s["score"] < 3.0]
    below_30_str = ", ".join(f"{s['name']} ({s['score']}/3)" for s in below_30) or "none"

    prompt = f"""Write a bullet-point daily summary for the {data['center']} Mathnasium \
center director. This will appear at the top of the nightly briefing email.

Write 4-6 concise bullet points, one sentence each. Be specific — name students when relevant. \
Cover the most important points: standout performers, attendance highlights, instructor workload, \
Mathlete score trends, and any flags or concerns. \
Do NOT mention mastery checks — those are covered separately in the Academic Accomplishments section. \
Start each bullet with an em dash (–). Write only the bullets — no greeting, heading, or sign-off.

Data from {data['report_date']}:
- Sessions: {data['total_sessions']}, Unique students: {data['unique_students']}
- Total pages completed: {data['total_pages']}, Avg Mathlete score: {data['avg_score']}/3
- Students below 3.0 Mathlete: {below_30_str}
- Beat page goal: {beat}
- Below page goal: {below}
- Instructors: {instructors}
- Instructor-flagged internal notes: {flags}
- Missing LP assignments: {missing_lp}
- Peak attendance: {next((b['label'] for b in data['att_buckets'] if b['peak']), 'N/A')} \
({next((b['count'] for b in data['att_buckets'] if b['peak']), 0)} students)"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system="You are a Mathnasium center director assistant. Write concise, specific briefing summaries.",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ─── STANDOUT SESSIONS ────────────────────────────────────────────────────────

def generate_standouts(data: dict) -> list[dict]:
    """Returns a list of {name, highlight, quote} dicts."""
    session_lines = "\n".join(
        f"{s['name']} | pages {s['pages']}/{s['goal'] or 'N/A'} | "
        f"mastered: {', '.join(s['mastered']) or 'none'} | "
        f"notes: \"{s['session_notes']}\""
        for s in data["sessions"]
    )

    prompt = f"""Identify the top 3-5 standout student sessions from the list below. \
Only include students with a genuine breakthrough: mastery check completed, significantly \
beat their page goal, or instructor notes describing impressive progress.

For each standout, output exactly this format (no extra text):
NAME: [student name]
HIGHLIGHT: [one sentence describing their specific breakthrough]
QUOTE: [a short phrase under 15 words taken directly from their session notes]

Sessions:
{session_lines}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system="You are a Mathnasium academic coach identifying standout student sessions. Be specific and cite evidence.",
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    standouts = []
    for block in re.split(r'(?=NAME:)', text):
        block = block.strip()
        if not block:
            continue
        name      = (re.search(r'NAME:\s*(.+)', block) or [None, ""])[1].strip()  # type: ignore
        highlight = (re.search(r'HIGHLIGHT:\s*(.+)', block) or [None, ""])[1].strip()  # type: ignore
        quote     = (re.search(r'QUOTE:\s*(.+)', block) or [None, ""])[1].strip()  # type: ignore
        if name and highlight:
            standouts.append({"name": name, "highlight": highlight, "quote": quote})

    return standouts


# ─── SESSION QUALITY ──────────────────────────────────────────────────────────

def generate_session_quality(data: dict) -> dict:
    """
    Returns:
    {
        academic:  [{name, reason}, ...],
        behavioral: [{name, reason}, ...],
        qc:        [{name, reason}, ...],
    }
    """
    session_lines = "\n---\n".join(
        f"Student: {s['name']}\n"
        f"Session notes: \"{s['session_notes']}\"\n"
        f"Pages: {s['pages']}/{s['goal'] or 'N/A'}\n"
        f"LP assigned: {'yes' if s['lp_assigned'] else 'NO - MISSING'}"
        for s in data["sessions"]
    )

    prompt = f"""Analyze each student session below and flag genuine issues in these three categories:

ACADEMIC — student is struggling, confused, or significantly below page goal with no explanation \
in the notes. Look for: "confused", "struggled", "didn't understand", "needs help", pages far \
below goal with no mastery or special circumstance mentioned.

BEHAVIORAL — behavioral concerns explicitly mentioned. Look for: "distracted", "frustrated", \
"difficult", "resistant", "behavior concern", "wouldn't focus".

QC — session summary note is not suitable to share with parents: too short (under one full sentence), \
purely generic ("had a great session" with zero specifics), or missing entirely.

For each flag, output exactly:
CATEGORY: [ACADEMIC or BEHAVIORAL or QC]
STUDENT: [name]
REASON: [one sentence explanation]

Only flag genuine issues. If a category has no flags, output nothing for it.

Sessions:
{session_lines}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system="You are a QC system for a Mathnasium learning center. Flag real issues only. Do not flag positive sessions.",
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    flags: dict = {"academic": [], "behavioral": [], "qc": []}

    for block in re.split(r'(?=CATEGORY:)', text):
        block = block.strip()
        if not block:
            continue
        cat_match = re.search(r'CATEGORY:\s*(\w+)', block, re.IGNORECASE)
        stu_match = re.search(r'STUDENT:\s*(.+)',   block, re.IGNORECASE)
        rsn_match = re.search(r'REASON:\s*(.+)',    block, re.IGNORECASE)
        if not (cat_match and stu_match):
            continue
        cat = cat_match.group(1).lower()
        if cat in flags:
            flags[cat].append({
                "name":   stu_match.group(1).strip(),
                "reason": rsn_match.group(1).strip() if rsn_match else "",
            })

    return flags


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

def generate_all(data: dict) -> dict:
    """Run all three AI calls and return a combined dict."""
    print("[generate] Writing executive summary ...")
    summary = generate_executive_summary(data)

    print("[generate] Identifying standout sessions ...")
    standouts = generate_standouts(data)

    print("[generate] Analyzing session quality ...")
    quality = generate_session_quality(data)

    return {
        "executive_summary": summary,
        "standouts":         standouts,
        "quality":           quality,
    }


if __name__ == "__main__":
    import sys, json
    from parse import parse_report
    path = sys.argv[1] if len(sys.argv) > 1 else "downloads/radius_today.csv"
    data = parse_report(path)
    ai   = generate_all(data)
    print(json.dumps(ai, indent=2))

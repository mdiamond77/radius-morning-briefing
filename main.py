"""
main.py
Orchestrates the full nightly pipeline:
  1. Scrape Radius DWP report → download Excel
  2. Scrape Radius Enrollment report → download Excel
  3. Parse both reports
  4. Generate AI content via Claude API
  5. Render + send HTML email

Run manually:   python main.py
Specify center: python main.py --center Englewood
Use local file: python main.py --xlsx path/to/dwp.xlsx --enrollment path/to/enrollment.xlsx
"""

import argparse
import os
import subprocess
from datetime import date, timedelta

from parse            import parse_report
from parse_enrollment import parse_enrollment_report
from generate         import generate_all
from send             import send_report
from history          import append_entry, get_recent


def run(center_name: str = None, xlsx_path: str = None,
        enrollment_path: str = None, report_date: date = None):

    if report_date is None:
        # GitHub Actions runs in UTC. At 11 PM Eastern (3 AM UTC),
        # the server date is already the next calendar day.
        # So we always report on yesterday (UTC) = today (Eastern).
        report_date = date.today() - timedelta(days=1)
    if center_name is None:
        center_name = os.environ.get("CENTER_NAME", "Teaneck")

    # ── Step 1: Scrape DWP report ──────────────────────────────────────────────
    if xlsx_path is None:
        print(f"=== Step 1: Scraping DWP report for {center_name} ===")
        from scrape import scrape_radius_report
        xlsx_path = scrape_radius_report(center_name, report_date)
    else:
        print(f"=== Step 1: Using provided DWP file: {xlsx_path} ===")

    # ── Step 2: Scrape enrollment report ───────────────────────────────────────
    if enrollment_path is None:
        print("=== Step 2: Scraping enrollment report ===")
        from scrape_enrollment import scrape_enrollment_report
        enrollment_path = scrape_enrollment_report(report_date)
    else:
        print(f"=== Step 2: Using provided enrollment file: {enrollment_path} ===")

    # ── Step 3: Parse both reports ─────────────────────────────────────────────
    print("=== Step 3: Parsing reports ===")
    enrollment_data = parse_enrollment_report(enrollment_path, center_name, report_date)

    # Build set of currently enrolled private students from enrollment data
    private_students = set()
    try:
        from openpyxl import load_workbook as _lwb
        _wb = _lwb(enrollment_path)
        _ws = _wb.active
        _hdrs = [c.value for c in _ws[1]]
        for _row in _ws.iter_rows(min_row=2, values_only=True):
            _r = dict(zip(_hdrs, _row))
            if (_r.get("Center") or "").strip() == center_name and \
               _r.get("Status") in ("Enrolled", "On Hold") and \
               "private" in (_r.get("Membership Type") or "").lower():
                _name = f"{(_r.get('Student First Name') or '').strip()} {(_r.get('Student Last Name') or '').strip()}".strip()
                private_students.add(_name)
    except Exception as e:
        print(f"    Warning: could not build private student list — {e}")

    data = parse_report(xlsx_path, report_date, private_students=private_students)

    if not data or not data.get("total_sessions"):
        print(f"    No sessions found for {center_name} on {report_date} — skipping email.")
        return

    print(f"    DWP: {data['total_sessions']} sessions, {data['unique_students']} students ({data.get('private_sessions', 0)} private)")
    print(f"    Enrollment: {len(enrollment_data['this_month'])} new this month, roster {enrollment_data['active_roster']}")

    # ── Step 4: Generate AI content ────────────────────────────────────────────
    print("=== Step 4: Generating AI content ===")
    ai = generate_all(data)
    print("    Executive summary, standouts, and QC analysis complete.")

    # Load history before appending today so the email shows the prior 7 days
    history = get_recent(center_name, days=7)

    # ── Step 5: Send ───────────────────────────────────────────────────────────
    print("=== Step 5: Sending email ===")
    send_report(data, ai, enrollment_data, report_date, history=history)

    # ── Step 6: Persist daily stats to history.json ────────────────────────────
    print("=== Step 6: Updating history ===")
    append_entry(
        center         = center_name,
        report_date    = report_date,
        total_sessions = data["total_sessions"],
        total_pages    = data["total_pages"],
        avg_score      = data["avg_score"],
    )
    if os.environ.get("GITHUB_ACTIONS"):
        try:
            subprocess.run(["git", "config", "user.name",  "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
            subprocess.run(["git", "add", "history.json"], check=True)
            result = subprocess.run(["git", "diff", "--cached", "--quiet"])
            if result.returncode != 0:
                subprocess.run(["git", "commit", "-m", f"chore: update history for {center_name} {report_date} [skip ci]"], check=True)
                # Pull rebase first in case the parallel job already pushed
                subprocess.run(["git", "pull", "--rebase"], check=True)
                subprocess.run(["git", "push"], check=True)
                print("[history] Committed and pushed history.json")
            else:
                print("[history] No changes to history.json")
        except Exception as e:
            print(f"[history] Warning: could not commit history — {e}")

    print("=== Done. ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Radius Daily Summary Automation")
    parser.add_argument("--center",     help="Center name: Teaneck or Englewood", default=None)
    parser.add_argument("--xlsx",       help="Path to DWP Excel file (skips scraping)", default=None)
    parser.add_argument("--enrollment", help="Path to enrollment Excel file (skips scraping)", default=None)
    parser.add_argument("--date",       help="Report date as YYYY-MM-DD (defaults to today)", default=None)
    args = parser.parse_args()

    report_date = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    run(center_name=args.center, xlsx_path=args.xlsx,
        enrollment_path=args.enrollment, report_date=report_date)

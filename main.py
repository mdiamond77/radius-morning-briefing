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
from datetime import date

from parse            import parse_report
from parse_enrollment import parse_enrollment_report
from generate         import generate_all
from send             import send_report


def run(center_name: str = None, xlsx_path: str = None,
        enrollment_path: str = None, report_date: date = None):

    if report_date is None:
        report_date = date.today()
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
    data            = parse_report(xlsx_path, report_date)
    enrollment_data = parse_enrollment_report(enrollment_path, center_name, report_date)

    if not data or not data.get("total_sessions"):
        print(f"    No sessions found for {center_name} on {report_date} — skipping email.")
        return

    print(f"    DWP: {data['total_sessions']} sessions, {data['unique_students']} students")
    print(f"    Enrollment: {len(enrollment_data['this_month'])} new this month, roster {enrollment_data['active_roster']}")

    # ── Step 4: Generate AI content ────────────────────────────────────────────
    print("=== Step 4: Generating AI content ===")
    ai = generate_all(data)
    print("    Executive summary, standouts, and QC analysis complete.")

    # ── Step 5: Send ───────────────────────────────────────────────────────────
    print("=== Step 5: Sending email ===")
    send_report(data, ai, enrollment_data, report_date)
    print("=== Done. ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Radius Daily Summary Automation")
    parser.add_argument("--center",     help="Center name: Teaneck or Englewood", default=None)
    parser.add_argument("--xlsx",       help="Path to DWP Excel file (skips scraping)", default=None)
    parser.add_argument("--enrollment", help="Path to enrollment Excel file (skips scraping)", default=None)
    parser.add_argument("--date",       help="Report date as YYYY-MM-DD (defaults to today)", default=None)
    args = parser.parse_args()

    report_date = date.fromisoformat(args.date) if args.date else date.today()
    run(center_name=args.center, xlsx_path=args.xlsx,
        enrollment_path=args.enrollment, report_date=report_date)

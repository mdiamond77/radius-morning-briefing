"""
main.py
Orchestrates the full nightly pipeline:
  1. Scrape Radius → download Excel for the given center
  2. Parse Excel → structured data
  3. Generate AI content via Claude API
  4. Render + send HTML email
"""

import argparse
import os
from datetime import date

from parse    import parse_report
from generate import generate_all
from send     import send_report


def run(center_name: str = None, xlsx_path: str = None, report_date: date = None):
    if report_date is None:
        report_date = date.today()

    if center_name is None:
        center_name = os.environ.get("CENTER_NAME", "Teaneck")

    # ── Step 1: Scrape (or use provided file) ─────────────────────────────────
    if xlsx_path is None:
        print(f"=== Step 1: Scraping Radius for {center_name} ===")
        from scrape import scrape_radius_report
        xlsx_path = scrape_radius_report(center_name, report_date)
    else:
        print(f"=== Step 1: Using provided file: {xlsx_path} ===")

    # ── Step 2: Parse ─────────────────────────────────────────────────────────
    print("=== Step 2: Parsing report ===")
    data = parse_report(xlsx_path, report_date)
    print(f"    {data['total_sessions']} sessions, {data['unique_students']} students parsed.")

    # ── Step 3: Generate AI content ───────────────────────────────────────────
    print("=== Step 3: Generating AI content ===")
    ai = generate_all(data)
    print("    Executive summary, standouts, and QC analysis complete.")

    # ── Step 4: Send ──────────────────────────────────────────────────────────
    print("=== Step 4: Sending email ===")
    send_report(data, ai, report_date)
    print("=== Done. ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Radius Morning Briefing Automation")
    parser.add_argument("--center", help="Center name: Teaneck or Englewood", default=None)
    parser.add_argument("--xlsx",   help="Path to Excel file (skips scraping)", default=None)
    parser.add_argument("--date",   help="Report date as YYYY-MM-DD (defaults to today)", default=None)
    args = parser.parse_args()

    report_date = date.fromisoformat(args.date) if args.date else date.today()
    run(center_name=args.center, xlsx_path=args.xlsx, report_date=report_date)

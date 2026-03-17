"""
main.py
Orchestrates the full nightly pipeline:
  1. Scrape Radius → download CSV
  2. Parse CSV → structured data
  3. Generate AI content via Claude API
  4. Render + send HTML email

Run manually:  python main.py
Run with file: python main.py --csv path/to/file.csv   (skips scraping, useful for testing)
"""

import argparse
import sys
from datetime import date

from parse    import parse_report
from generate import generate_all
from send     import send_report


def run(csv_path: str = None, report_date: date = None):
    if report_date is None:
        report_date = date.today()

    # ── Step 1: Scrape (or use provided CSV) ─────────────────────────────────
    if csv_path is None:
        print("=== Step 1: Scraping Radius ===")
        from scrape import scrape_radius_report
        csv_path = scrape_radius_report(report_date)
    else:
        print(f"=== Step 1: Using provided CSV: {csv_path} ===")

    # ── Step 2: Parse ─────────────────────────────────────────────────────────
    print("=== Step 2: Parsing CSV ===")
    data = parse_report(csv_path, report_date)
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
    parser.add_argument("--csv", help="Path to CSV file (skips Radius scraping)", default=None)
    parser.add_argument("--date", help="Report date as YYYY-MM-DD (defaults to today)", default=None)
    args = parser.parse_args()

    report_date = date.fromisoformat(args.date) if args.date else date.today()
    run(csv_path=args.csv, report_date=report_date)

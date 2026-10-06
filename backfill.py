"""
backfill.py
One-time script to seed history.json with the past 7 days of DWP data.
Run once per center:
    python backfill.py --center Teaneck
    python backfill.py --center Englewood
Days with no sessions are skipped automatically.
"""

import argparse
import os
from datetime import date, timedelta

from scrape   import scrape_radius_report
from parse    import parse_report
from history  import append_entry


def backfill(center_name: str, days: int = 7):
    today = date.today()
    # yesterday back through (yesterday - days + 1); skip today since
    # the nightly run will add it tonight
    dates = [today - timedelta(days=i) for i in range(1, days + 1)]

    for target_date in dates:
        print(f"\n=== Backfilling {center_name} for {target_date} ===")
        try:
            xlsx_path = scrape_radius_report(center_name, target_date)
            data = parse_report(xlsx_path, target_date)
            if not data or not data.get("total_sessions"):
                print(f"    No sessions — skipping.")
                continue
            append_entry(
                center       = center_name,
                report_date  = target_date,
                total_sessions = data["total_sessions"],
                total_pages  = data["total_pages"],
                avg_score    = data["avg_score"],
            )
        except Exception as e:
            print(f"    Error on {target_date}: {e} — skipping.")

    print(f"\n=== Backfill complete for {center_name} ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill history.json")
    parser.add_argument("--center", required=True, help="Center name: Teaneck or Englewood")
    parser.add_argument("--days",   type=int, default=7, help="Number of past days to backfill")
    args = parser.parse_args()
    backfill(args.center, args.days)

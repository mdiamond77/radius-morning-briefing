"""
scrape.py
Logs into Radius, navigates to the daily session report, and downloads the CSV.

IMPORTANT: Before this script will work, you need to inspect your Radius site
and fill in the SELECTORS section below. Instructions are in README.md.
"""

import os
import time
from datetime import date
from playwright.sync_api import sync_playwright

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
RADIUS_URL      = os.environ["RADIUS_URL"]        # e.g. https://app.radiusapp.com
RADIUS_USERNAME = os.environ["RADIUS_USERNAME"]
RADIUS_PASSWORD = os.environ["RADIUS_PASSWORD"]
DOWNLOAD_DIR    = os.path.join(os.path.dirname(__file__), "downloads")

# ─── SELECTORS ────────────────────────────────────────────────────────────────
# These need to be filled in once you've inspected your Radius login page.
# Open Radius in Chrome, right-click each field, click "Inspect", and find
# the id or name attribute. Replace the placeholders below.
#
# Example: if the username field is <input id="user-email">, use "#user-email"

LOGIN_USERNAME_SELECTOR = "#username"       # ← update if different
LOGIN_PASSWORD_SELECTOR = "#password"       # ← update if different
LOGIN_BUTTON_SELECTOR   = "#login-button"   # ← update if different

# The URL of the daily session report page inside Radius
REPORT_URL = os.environ.get("RADIUS_REPORT_URL", "")  # e.g. https://app.radiusapp.com/reports/sessions

# The selector for the CSV/Excel export button on the report page
EXPORT_BUTTON_SELECTOR  = "#export-csv"     # ← update after inspecting Radius
# ──────────────────────────────────────────────────────────────────────────────


def scrape_radius_report(target_date: date = None) -> str:
    """
    Logs into Radius, runs the daily session report for target_date,
    downloads the CSV, and returns the local file path.
    """
    if target_date is None:
        target_date = date.today()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    date_str = target_date.strftime("%m/%d/%Y")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # ── Step 1: Log in ────────────────────────────────────────────────────
        print(f"[scrape] Navigating to {RADIUS_URL} ...")
        page.goto(RADIUS_URL)
        page.wait_for_load_state("networkidle")

        print("[scrape] Logging in ...")
        page.fill(LOGIN_USERNAME_SELECTOR, RADIUS_USERNAME)
        page.fill(LOGIN_PASSWORD_SELECTOR, RADIUS_PASSWORD)
        page.click(LOGIN_BUTTON_SELECTOR)
        page.wait_for_load_state("networkidle")

        # ── Step 2: Navigate to report ────────────────────────────────────────
        print(f"[scrape] Navigating to report page ...")
        page.goto(REPORT_URL)
        page.wait_for_load_state("networkidle")

        # ── Step 3: Set date filter to today ──────────────────────────────────
        # Adjust this block once you know what the date filter looks like in Radius.
        # Common patterns:
        #   page.fill("#date-from", date_str)
        #   page.fill("#date-to", date_str)
        #   page.select_option("#date-range", "today")
        print(f"[scrape] Setting date filter to {date_str} ...")
        # TODO: add your date filter interaction here

        # ── Step 4: Run report & wait for results ─────────────────────────────
        # page.click("#run-report")
        # page.wait_for_selector(".report-results-table")
        # TODO: update selectors for your report run button and results

        # ── Step 5: Download CSV ──────────────────────────────────────────────
        print("[scrape] Downloading CSV ...")
        with page.expect_download() as download_info:
            page.click(EXPORT_BUTTON_SELECTOR)
        download = download_info.value

        file_path = os.path.join(DOWNLOAD_DIR, f"radius_{target_date.isoformat()}.csv")
        download.save_as(file_path)
        print(f"[scrape] Saved to {file_path}")

        browser.close()

    return file_path


if __name__ == "__main__":
    path = scrape_radius_report()
    print(f"Downloaded: {path}")

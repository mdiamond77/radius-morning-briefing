"""
scrape_enrollment.py
Logs into Radius, navigates to the Enrollment Report, sets the date range
to 2018-01-01 through today, downloads the full Excel export (both centers),
and returns the local file path.
"""

import os
from datetime import date
from playwright.sync_api import sync_playwright

RADIUS_LOGIN_URL      = "https://radius.mathnasium.com"
RADIUS_ENROLLMENT_URL = "https://radius.mathnasium.com/Enrollment/EnrollmentReport"
RADIUS_USERNAME       = os.environ["RADIUS_USERNAME"]
RADIUS_PASSWORD       = os.environ["RADIUS_PASSWORD"]
DOWNLOAD_DIR          = os.path.join(os.path.dirname(__file__), "downloads")


def scrape_enrollment_report(target_date: date = None) -> str:
    """
    Downloads the full enrollment history (both centers, from Jan 1 2018)
    and returns the local file path.
    """
    if target_date is None:
        target_date = date.today()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    end_str   = target_date.strftime("%m/%d/%Y")
    start_str = "01/01/2018"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page    = context.new_page()

        # ── Step 1: Log in ────────────────────────────────────────────────────
        print("[enroll-scrape] Logging into Radius ...")
        page.goto(RADIUS_LOGIN_URL)
        page.wait_for_load_state("networkidle")
        page.fill("#UserName", RADIUS_USERNAME)
        page.fill("#Password", RADIUS_PASSWORD)
        page.click("#login")
        page.wait_for_load_state("networkidle")
        print("[enroll-scrape] Logged in.")

        # ── Step 2: Navigate to enrollment report ─────────────────────────────
        print("[enroll-scrape] Navigating to enrollment report ...")
        page.goto(RADIUS_ENROLLMENT_URL)
        page.wait_for_load_state("networkidle")

        # ── Step 3: Set date range ────────────────────────────────────────────
        # NOTE: Inspect the date fields on the enrollment report page and
        # update these selectors if they differ from the DWP report.
        print(f"[enroll-scrape] Setting date range {start_str} to {end_str} ...")
        try:
            page.fill("#StartDate", start_str)
            page.fill("#EndDate",   end_str)
        except Exception as e:
            print(f"[enroll-scrape] Warning: could not set dates — {e}")

        # ── Step 4: Click Search ──────────────────────────────────────────────
        print("[enroll-scrape] Running search ...")
        page.click("#btnsearch")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # ── Step 5: Download Excel export ─────────────────────────────────────
        print("[enroll-scrape] Downloading Excel export ...")
        with page.expect_download() as download_info:
            page.click("#dwpExcelBtn")
        download = download_info.value

        file_path = os.path.join(
            DOWNLOAD_DIR,
            f"enrollment_{target_date.isoformat()}.xlsx"
        )
        download.save_as(file_path)
        print(f"[enroll-scrape] Saved to {file_path}")

        browser.close()

    return file_path


if __name__ == "__main__":
    path = scrape_enrollment_report()
    print(f"Downloaded: {path}")

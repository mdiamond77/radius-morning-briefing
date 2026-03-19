"""
scrape.py
Logs into Radius, selects the center, runs the DWP report, and downloads the Excel file.
All selectors are confirmed from inspection of radius.mathnasium.com.
"""

import os
from datetime import date
from playwright.sync_api import sync_playwright

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
RADIUS_LOGIN_URL  = "https://radius.mathnasium.com"
RADIUS_REPORT_URL = "https://radius.mathnasium.com/DigitalWorkoutPlan/Report"
RADIUS_USERNAME   = os.environ["RADIUS_USERNAME"]
RADIUS_PASSWORD   = os.environ["RADIUS_PASSWORD"]
DOWNLOAD_DIR      = os.path.join(os.path.dirname(__file__), "downloads")

# Center values from the AllCenterListMultiSelect dropdown
CENTER_VALUES = {
    "Teaneck":   "2871",
    "Englewood": "2428",
}
# ──────────────────────────────────────────────────────────────────────────────


def scrape_radius_report(center_name: str, target_date: date = None) -> str:
    """
    Logs into Radius, selects the given center, runs the DWP report for
    target_date, downloads the Excel file, and returns the local file path.
    """
    if target_date is None:
        target_date = date.today()

    if center_name not in CENTER_VALUES:
        raise ValueError(f"Unknown center: {center_name}. Must be one of {list(CENTER_VALUES.keys())}")

    center_value = CENTER_VALUES[center_name]
    date_str     = target_date.strftime("%m/%d/%Y")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page    = context.new_page()

        # ── Step 1: Log in ────────────────────────────────────────────────────
        print(f"[scrape] Logging into Radius ...")
        page.goto(RADIUS_LOGIN_URL)
        page.wait_for_load_state("networkidle")

        page.fill("#UserName", RADIUS_USERNAME)
        page.fill("#Password", RADIUS_PASSWORD)
        page.click("#login")
        page.wait_for_load_state("networkidle")
        print("[scrape] Logged in successfully.")

        # ── Step 2: Navigate to report page ───────────────────────────────────
        print(f"[scrape] Navigating to DWP report ...")
        page.goto(RADIUS_REPORT_URL)
        page.wait_for_load_state("networkidle")

        # ── Step 3: Select center from Kendo multiselect ──────────────────────
        # The underlying <select> is hidden by Kendo UI, so we set its value
        # directly via JavaScript and trigger the change event so Kendo
        # registers the selection.
        print(f"[scrape] Selecting center: {center_name} ...")
        page.evaluate(f"""
            var widget = jQuery('#AllCenterListMultiSelect').data('kendoMultiSelect');
            widget.value(['{center_value}']);
            widget.trigger('change');
        """)
        page.wait_for_timeout(1000)

        # ── Step 4: Set date filter to target_date ────────────────────────────
        print(f"[scrape] Setting date filter to {date_str} ...")
        try:
            js_date = target_date.strftime("%B %-d, %Y")
            page.evaluate(f"""
                var startPicker = jQuery('#dwpFromDate').data('kendoDatePicker');
                var endPicker   = jQuery('#dwpToDate').data('kendoDatePicker');
                if (startPicker) {{
                    startPicker.value(new Date('{js_date}'));
                    startPicker.trigger('change');
                }}
                if (endPicker) {{
                    endPicker.value(new Date('{js_date}'));
                    endPicker.trigger('change');
                }}
            """)
            page.wait_for_timeout(500)
            # Verify the date was set
            actual = page.input_value("#dwpFromDate")
            print(f"[scrape] Date field now shows: {actual}")
        except Exception as e:
            print(f"[scrape] Warning: could not set date filter — {e}")

        # ── Step 5: Click Search ──────────────────────────────────────────────
        print("[scrape] Running search ...")
        page.click("#btnsearch")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # ── Step 6: Download Excel export ─────────────────────────────────────
        print("[scrape] Downloading Excel export ...")
        with page.expect_download() as download_info:
            page.click("#dwpExcelBtn")
        download = download_info.value

        file_path = os.path.join(
            DOWNLOAD_DIR,
            f"radius_{center_name.lower()}_{target_date.isoformat()}.xlsx"
        )
        download.save_as(file_path)
        print(f"[scrape] Saved to {file_path}")

        browser.close()

    return file_path


if __name__ == "__main__":
    import sys
    center = sys.argv[1] if len(sys.argv) > 1 else "Teaneck"
    path   = scrape_radius_report(center)
    print(f"Downloaded: {path}")

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
    # JavaScript Date constructor format
    start_js  = "January 1, 2018"
    end_js    = target_date.strftime("%B %-d, %Y")

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
        print(f"[enroll-scrape] Setting date range {start_str} to {end_str} ...")
        try:
            page.evaluate(f"""
                var startPicker = jQuery('#StartDate').data('kendoDatePicker');
                var endPicker   = jQuery('#EndDate').data('kendoDatePicker');
                startPicker.value(new Date('{start_js}'));
                startPicker.trigger('change');
                endPicker.value(new Date('{end_js}'));
                endPicker.trigger('change');
            """)
            page.wait_for_timeout(500)
        except Exception as e:
            print(f"[enroll-scrape] Warning: could not set dates — {e}")

        # ── Step 4: Select both centers ───────────────────────────────────────
        # Download all centers in one file — we filter by center in code
        print("[enroll-scrape] Selecting all centers ...")
        try:
            page.evaluate("""
                var widget = jQuery('#AllCenterListMultiSelect').data('kendoMultiSelect');
                widget.value(['2871', '2428']);
                widget.trigger('change');
            """)
            page.wait_for_timeout(1000)
        except Exception as e:
            print(f"[enroll-scrape] Warning: could not set centers — {e}")

        # ── Step 5: Click Search ──────────────────────────────────────────────
        print("[enroll-scrape] Running search ...")
        page.click("#btnsearch")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(8000)

        # Wait for the export button to become truly enabled
        # (it starts disabled and enables only after results finish rendering)
        print("[enroll-scrape] Waiting for export button to enable ...")
        try:
            page.wait_for_function(
                "() => !document.getElementById('btnExport').hasAttribute('disabled')",
                timeout=60000
            )
            print("[enroll-scrape] Export button is now enabled.")
        except Exception as e:
            print(f"[enroll-scrape] Warning: export button may still be disabled — {e}")

        # ── Step 6: Download Excel export ─────────────────────────────────────
        print("[enroll-scrape] Downloading Excel export ...")

        # Inspect the button's onclick and any Kendo widget attached to it
        btn_info = page.evaluate("""() => {
            var btn = document.getElementById('btnExport');
            if (!btn) return {error: 'button not found'};
            var widget = jQuery(btn).data('kendoButton');
            return {
                disabled: btn.disabled,
                hasAttribute: btn.hasAttribute('disabled'),
                onclick: btn.getAttribute('onclick'),
                outerHTML: btn.outerHTML.substring(0, 300),
                hasKendo: !!widget,
                parentForm: btn.closest('form') ? btn.closest('form').action : 'no form',
            };
        }""")
        print(f"[enroll-scrape] Button info: {btn_info}")

        # Take a screenshot to see page state
        screenshot_path = os.path.join(DOWNLOAD_DIR, "enrollment_page.png")
        page.screenshot(path=screenshot_path)
        print(f"[enroll-scrape] Screenshot saved to {screenshot_path}")

        # Set up response listener BEFORE clicking
        all_responses = []
        file_saved = {"path": None}

        def handle_response(response):
            ct = response.headers.get("content-type", "")
            all_responses.append(f"[{response.status}] {ct[:60]} | {response.url[-100:]}")
            if any(x in ct for x in ["excel", "spreadsheet", "octet", "download", "zip"]):
                try:
                    body = response.body()
                    fp = os.path.join(DOWNLOAD_DIR, f"enrollment_{target_date.isoformat()}.xlsx")
                    with open(fp, "wb") as f:
                        f.write(body)
                    file_saved["path"] = fp
                    print(f"[enroll-scrape] FILE SAVED via interception: {len(body)} bytes")
                except Exception as e:
                    print(f"[enroll-scrape] Could not save intercepted file: {e}")

        page.on("response", handle_response)

        # Try standard download
        try:
            with page.expect_download(timeout=30000) as dl:
                page.click("#btnExport")
            fp = os.path.join(DOWNLOAD_DIR, f"enrollment_{target_date.isoformat()}.xlsx")
            dl.value.save_as(fp)
            print(f"[enroll-scrape] Saved via download event: {fp}")
            browser.close()
            return fp
        except Exception as e1:
            print(f"[enroll-scrape] Download event failed: {e1}")

        # Wait and check if interception caught anything
        page.wait_for_timeout(10000)
        if file_saved["path"]:
            browser.close()
            return file_saved["path"]

        # Log all responses we saw
        print(f"[enroll-scrape] Responses after click ({len(all_responses)}):")
        for r in all_responses[-30:]:
            print(f"  {r}")

        browser.close()
        raise RuntimeError("Could not download enrollment report — see logs above.")

        browser.close()
        raise RuntimeError(
            "Could not download enrollment report — button clicked but no file received. "
            f"Page URL after click: {current_url}"
        )

    return file_path


if __name__ == "__main__":
    path = scrape_enrollment_report()
    print(f"Downloaded: {path}")

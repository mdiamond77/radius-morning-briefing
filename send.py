"""
send.py
Renders the Daily Summary HTML email and sends it via SMTP.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER     = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
RECIPIENTS    = os.environ["REPORT_RECIPIENTS"]
CENTER_NAME   = os.environ.get("CENTER_NAME", "Teaneck")

# Logo hosted on GitHub — update YOUR_GITHUB_USERNAME below
GITHUB_USER   = os.environ.get("GH_USERNAME", "YOUR_GITHUB_USERNAME")
LOGO_URL      = f"https://raw.githubusercontent.com/{GITHUB_USER}/radius-morning-briefing/main/logo.jpg"
# ──────────────────────────────────────────────────────────────────────────────


def render_email(data: dict, ai: dict) -> str:

    # ── Helpers ───────────────────────────────────────────────────────────────
    def stat_box(label, value):
        return f"""
        <td style="padding:0 6px 0 0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px 10px;text-align:center;">
            <div style="font-size:12px;color:#666;margin-bottom:6px;">{label}</div>
            <div style="font-size:28px;font-weight:700;color:#1a1a1a;line-height:1;">{value}</div>
          </div>
        </td>"""

    def section(title, subtitle=""):
        sub = f'<div style="font-size:12px;color:#777;font-style:italic;margin-top:3px;">{subtitle}</div>' if subtitle else ""
        return f"""
        <div style="border:1px solid #e8e8e8;border-left:4px solid #c8271e;border-radius:0 8px 8px 0;margin-bottom:20px;overflow:hidden;">
          <div style="padding:13px 20px 10px;background:#fafafa;border-bottom:1px solid #f0f0f0;">
            <div style="font-size:15px;font-weight:700;color:#1a1a1a;">{title}</div>{sub}
          </div>
          <div style="padding:16px 20px;">"""

    def section_end():
        return "</div></div>"

    def ok(msg):
        return f'<p style="font-size:13px;font-style:italic;color:#166534;margin:4px 0;">&#10003; {msg}</p>'

    def subh(text, color="#1a1a1a", mt=14):
        return f'<p style="font-size:13px;font-weight:700;color:{color};margin:{mt}px 0 8px;">{text}</p>'

    # ── Attendance rows ────────────────────────────────────────────────────────
    att_rows = ""
    max_s = max((b["count"] for b in data["att_buckets"]), default=1)
    for b in data["att_buckets"]:
        pct   = round(b["count"] / max_s * 100)
        ratio = b.get("ratio")
        ratio_str = f"{ratio}:1" if ratio else "—"
        # color-code ratio: ≤2 green, ≤3 amber, >3 red
        if ratio and ratio <= 2.0:
            ratio_color = "#166534"
        elif ratio and ratio <= 3.0:
            ratio_color = "#854F0B"
        else:
            ratio_color = "#991b1b"

        peak_tag = ' <span style="background:#c8271e;color:#fff;border-radius:3px;padding:1px 6px;font-size:10px;font-weight:700;">Peak</span>' if b["peak"] else ""
        bar_opacity = "1.0" if b["peak"] else "0.35"

        att_rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #f5f5f5;font-size:13px;color:#555;white-space:nowrap;">
            {b['label']}{peak_tag}
          </td>
          <td style="padding:8px;border-bottom:1px solid #f5f5f5;width:120px;">
            <div style="background:#f0f0f0;border-radius:3px;height:12px;overflow:hidden;">
              <div style="background:#c8271e;opacity:{bar_opacity};height:100%;width:{pct}%;border-radius:3px;"></div>
            </div>
          </td>
          <td style="padding:8px;border-bottom:1px solid #f5f5f5;font-size:13px;font-weight:700;text-align:center;">{b['count']}</td>
          <td style="padding:8px;border-bottom:1px solid #f5f5f5;font-size:13px;font-weight:700;text-align:center;">{b.get('instructors', '—')}</td>
          <td style="padding:8px;border-bottom:1px solid #f5f5f5;font-size:13px;font-weight:700;text-align:center;color:{ratio_color};">{ratio_str}</td>
          <td style="padding:8px;border-bottom:1px solid #f5f5f5;font-size:11px;color:#888;">{', '.join(b['students'])}</td>
        </tr>"""

    # ── Mastery rows ───────────────────────────────────────────────────────────
    mastery_rows = ""
    for m in data["mastery_list"]:
        topics_html = "".join(
            f'<div style="margin:2px 0;"><span style="display:inline-block;background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:3px;padding:1px 6px;font-size:11px;font-weight:600;margin-right:4px;">&#10003; Mastered</span>{t}</div>'
            for t in m["topics"]
        )
        mastery_rows += f"""
        <tr>
          <td style="padding:10px 8px;border-bottom:1px solid #f0f0f0;font-weight:700;font-size:13px;vertical-align:top;white-space:nowrap;">{m['name']}</td>
          <td style="padding:10px 8px;border-bottom:1px solid #f0f0f0;font-size:13px;">{topics_html}</td>
        </tr>"""

    # ── Standout sessions ──────────────────────────────────────────────────────
    standouts_html = ""
    for s in ai.get("standouts", []):
        quote_html = f'<div style="font-style:italic;color:#666;font-size:12px;margin-top:6px;padding-left:12px;border-left:3px solid #e0e0e0;">&ldquo;{s["quote"]}&rdquo;</div>' if s.get("quote") else ""
        standouts_html += f"""
        <div style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
          <div style="font-weight:700;font-size:14px;">{s['name']}</div>
          <div style="font-size:13px;color:#444;margin-top:3px;">{s['highlight']}</div>
          {quote_html}
        </div>"""
    if not standouts_html:
        standouts_html = ok("No standout sessions identified.")

    # ── Internal notes ─────────────────────────────────────────────────────────
    internal_html = ""
    for n in data["internal_notes"]:
        internal_html += f"""
        <div style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
          <div style="font-weight:700;font-size:13px;">{n['name']}</div>
          <div style="font-size:13px;color:#444;margin-top:2px;">{n['note']}</div>
        </div>"""
    if not internal_html:
        internal_html = ok("No internal notes today &mdash; all systems ran smoothly!")

    # ── Instructor rows ────────────────────────────────────────────────────────
    instructor_rows = ""
    for i in data["instructor_summary"]:
        instructor_rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #f0f0f0;font-weight:700;font-size:13px;">{i['name']}</td>
          <td style="padding:8px;border-bottom:1px solid #f0f0f0;font-size:13px;">{i['count']}</td>
          <td style="padding:8px;border-bottom:1px solid #f0f0f0;font-size:12px;color:#666;">{', '.join(i['students'])}</td>
        </tr>"""

    # ── Session quality ────────────────────────────────────────────────────────
    quality = ai.get("quality", {"academic": [], "behavioral": [], "qc": []})

    def qc_box(label, count):
        color = "#c8271e" if count > 0 else "#166534"
        return f"""
        <td style="padding:0 6px 0 0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:12px 10px;text-align:center;">
            <div style="font-size:11px;color:#666;margin-bottom:4px;">{label}</div>
            <div style="font-size:26px;font-weight:700;color:{color};">{count}</div>
          </div>
        </td>"""

    def qc_section(title, color, items, empty):
        html = subh(title, color)
        if items:
            for item in items:
                html += f'<div style="padding:8px 0;border-bottom:1px solid #f0f0f0;"><div style="font-weight:700;font-size:13px;">{item["name"]}</div><div style="font-size:12px;color:#555;margin-top:2px;">{item["reason"]}</div></div>'
        else:
            html += ok(empty)
        return html

    # ── Full HTML ──────────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Daily Summary &mdash; {data['center']} &mdash; {data['report_date']}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f0;font-family:Arial,sans-serif;">
<div style="max-width:700px;margin:0 auto;background:#fff;">

  <!-- RED HEADER -->
  <div style="background:#c8271e;padding:16px 28px;display:flex;align-items:center;justify-content:space-between;">
    <img src="{LOGO_URL}" alt="Mathnasium" height="38" style="display:block;">
    <div style="text-align:right;color:#fff;font-size:12px;opacity:0.9;line-height:1.5;">
      Daily Summary Report<br><strong>{data['center']} Center</strong>
    </div>
  </div>

  <!-- TITLE -->
  <div style="background:#fff;border-bottom:1px solid #e8e8e8;padding:20px 28px 16px;">
    <div style="font-size:22px;font-weight:700;color:#1a1a1a;">Daily Summary</div>
    <div style="margin-top:6px;">
      <span style="display:inline-block;font-size:12px;font-weight:600;background:#fef2f2;color:#c8271e;border:1px solid #fcc;border-radius:4px;padding:2px 8px;">{data['center']}</span>
    </div>
    <div style="font-size:13px;color:#666;margin-top:6px;">{data['report_date']}</div>
  </div>

  <div style="padding:24px 28px;">

    <!-- DAILY SUMMARY (AI) -->
    {section("Daily Summary", "AI-generated overview of today&rsquo;s sessions")}
      <p style="font-size:13px;color:#555;margin-bottom:6px;font-style:italic;">&#9679; AI-generated</p>
      <p style="font-size:14px;line-height:1.75;color:#333;background:#fafafa;border-radius:6px;padding:16px 18px;margin:0;">
        {ai.get('executive_summary', 'Summary unavailable.')}
      </p>
    {section_end()}

    <!-- ENROLLMENTS PLACEHOLDER -->
    {section("New Enrollments", "Integration pending")}
      <div style="border:2px dashed #d0d0d0;border-radius:6px;padding:20px;text-align:center;color:#999;font-style:italic;font-size:13px;">
        Enrollment data will appear here once the enrollment system is connected.
      </div>
    {section_end()}

    <!-- ATTENDANCE -->
    {section("Attendance", "Half-hour occupancy with student-to-instructor ratio")}
      {subh("Session overview")}
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
        <tr>
          {stat_box("Total Sessions", data['total_sessions'])}
          {stat_box("Unique Students", data['unique_students'])}
        </tr>
      </table>
      {subh("By half-hour")}
      <table width="100%" cellpadding="0" cellspacing="0">
        <thead>
          <tr style="background:#fafafa;">
            <th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.4px;">Time</th>
            <th style="padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;width:120px;"></th>
            <th style="text-align:center;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.4px;">Students</th>
            <th style="text-align:center;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.4px;">Instructors</th>
            <th style="text-align:center;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.4px;">Ratio</th>
            <th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.4px;">Students</th>
          </tr>
        </thead>
        <tbody>{att_rows}</tbody>
      </table>
    {section_end()}

    <!-- ACADEMIC ACCOMPLISHMENTS -->
    {section("Academic Accomplishments", "Mastery checks trigger a celebratory parent text &mdash; ensure all are documented in DWP")}
      {subh("Today&rsquo;s learning metrics")}
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
        <tr>
          {stat_box("&#128218; Pages Completed", data['total_pages'])}
          {stat_box("&#127941; Mastery Checks", data['total_mastery'])}
          {stat_box("&#11088; Avg Mathlete Score", f"{data['avg_score']}/3" if data['avg_score'] else "N/A")}
        </tr>
      </table>
      {subh("Mastery achievements")}
      <table width="100%" cellpadding="0" cellspacing="0">
        <thead>
          <tr style="background:#fafafa;">
            <th style="text-align:left;padding:8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;width:35%;">Student</th>
            <th style="text-align:left;padding:8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Topics Mastered</th>
          </tr>
        </thead>
        <tbody>{mastery_rows}</tbody>
      </table>
      {subh("Standout sessions", mt=18)}
      <p style="font-size:13px;color:#555;margin-bottom:6px;font-style:italic;">&#9679; AI-generated</p>
      {standouts_html}
    {section_end()}

    <!-- INTERNAL NOTES -->
    {section("Internal Notes", "Instructor-flagged items for the Center Director")}
      {internal_html}
    {section_end()}

    <!-- INSTRUCTORS -->
    {section("Instructors", "Workload breakdown")}
      <table width="100%" cellpadding="0" cellspacing="0">
        <thead>
          <tr style="background:#fafafa;">
            <th style="text-align:left;padding:6px 8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Instructor</th>
            <th style="text-align:left;padding:6px 8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Students</th>
            <th style="text-align:left;padding:6px 8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Names</th>
          </tr>
        </thead>
        <tbody>{instructor_rows}</tbody>
      </table>
    {section_end()}

    <!-- SESSION QUALITY -->
    {section("Session Quality", "AI-detected flags from session notes")}
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
        <tr>
          {qc_box("Academic", len(quality["academic"]))}
          {qc_box("Behavioral", len(quality["behavioral"]))}
          {qc_box("QC Issues", len(quality["qc"]))}
          {qc_box("Missing LP", len(data["missing_lp"]))}
        </tr>
      </table>
      <p style="font-size:13px;color:#555;margin-bottom:6px;font-style:italic;">&#9679; AI-generated</p>
      {qc_section("Academic Concerns", "#d97706", quality["academic"], "No academic concerns to report today")}
      {qc_section("Behavioral Concerns", "#dc2626", quality["behavioral"], "No behavioral concerns to report today")}
      {qc_section("QC Issues", "#2563eb", quality["qc"], "No parent communication concerns to report today")}
      {subh("Missing LP Assignments", "#16a34a")}
      {''.join(f'<div style="padding:6px 0;font-size:13px;font-weight:700;color:#dc2626;">{n}</div>' for n in data['missing_lp']) or ok("All sessions have LP tracking documented")}
    {section_end()}

  </div>
</div>
</body>
</html>"""


def send_report(data: dict, ai: dict, report_date: date = None) -> None:
    if report_date is None:
        report_date = date.today()

    recipients = [r.strip() for r in RECIPIENTS.split(",") if r.strip()]
    subject    = f"Daily Summary \u2014 {CENTER_NAME} \u2014 {data['report_date']}"
    html_body  = render_email(data, ai)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    print(f"[send] Sending to: {', '.join(recipients)}")
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, recipients, msg.as_string())
    print("[send] Email sent successfully.")


if __name__ == "__main__":
    import sys
    from parse import parse_report
    from generate import generate_all
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "downloads/radius_today.xlsx"
    data = parse_report(csv_path)
    ai   = generate_all(data)
    send_report(data, ai)

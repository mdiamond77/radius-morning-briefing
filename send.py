"""
send.py
Renders the Morning Briefing HTML email from parsed data + AI content,
then sends it via SMTP (Gmail or any SMTP provider).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date


# ─── CONFIGURATION ────────────────────────────────────────────────────────────
SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER     = os.environ["SMTP_USER"]       # sending email address
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]   # Gmail App Password or SMTP password

RECIPIENTS    = os.environ["REPORT_RECIPIENTS"]  # comma-separated list of emails
CENTER_NAME   = os.environ.get("CENTER_NAME", "Teaneck")
# ──────────────────────────────────────────────────────────────────────────────


# ─── HTML TEMPLATE ────────────────────────────────────────────────────────────

def render_email(data: dict, ai: dict) -> str:
    """Render the full HTML email string."""

    # ── Helpers ───────────────────────────────────────────────────────────────
    def stat_card(label, value, sub=""):
        return f"""
        <td style="width:33%;padding:0 6px 0 0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px 10px;text-align:center;">
            <div style="font-size:12px;color:#666;margin-bottom:6px;">{label}</div>
            <div style="font-size:28px;font-weight:700;color:#1a1a1a;line-height:1;">{value}</div>
            {f'<div style="font-size:11px;color:#888;margin-top:4px;">{sub}</div>' if sub else ''}
          </div>
        </td>"""

    def section_start(title, subtitle="", left_color="#d4253a"):
        return f"""
        <div style="border:1px solid #e8e8e8;border-radius:8px;margin-bottom:20px;
                    border-left:4px solid {left_color};overflow:hidden;">
          <div style="padding:14px 20px 10px;background:#fafafa;border-bottom:1px solid #f0f0f0;">
            <div style="font-size:15px;font-weight:700;color:#1a1a1a;">{title}</div>
            {f'<div style="font-size:12px;color:#777;font-style:italic;margin-top:4px;">{subtitle}</div>' if subtitle else ''}
          </div>
          <div style="padding:16px 20px;">"""

    def section_end():
        return "</div></div>"

    def ok_line(msg):
        return f'<p style="font-size:13px;font-style:italic;color:#166534;margin:4px 0;">&#10003; {msg}</p>'

    def sub_heading(text, color="#1a1a1a"):
        return f'<p style="font-size:13px;font-weight:700;color:{color};margin:14px 0 8px;">{text}</p>'

    # ── Attendance table rows ──────────────────────────────────────────────────
    att_rows = ""
    for b in data["att_buckets"]:
        peak_tag = ' <span style="background:#fef9c3;color:#92400e;border:1px solid #fde68a;border-radius:3px;padding:1px 6px;font-size:11px;font-weight:600;">Peak</span>' if b["peak"] else ""
        att_rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #f0f0f0;font-size:13px;">{b['label']}{peak_tag}</td>
          <td style="padding:8px;border-bottom:1px solid #f0f0f0;font-size:13px;font-weight:700;">{b['count']}</td>
          <td style="padding:8px;border-bottom:1px solid #f0f0f0;font-size:12px;color:#666;">{', '.join(b['students'])}</td>
        </tr>"""

    # ── Mastery rows ───────────────────────────────────────────────────────────
    mastery_rows = ""
    for m in data["mastery_list"]:
        topics_html = "".join(
            f'<div style="margin:2px 0;"><span style="display:inline-block;background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:3px;padding:1px 7px;font-size:11px;font-weight:600;margin-right:4px;">&#10003; Mastered</span>{t}</div>'
            for t in m["topics"]
        )
        mastery_rows += f"""
        <tr>
          <td style="padding:10px 8px;border-bottom:1px solid #f0f0f0;font-weight:700;font-size:13px;vertical-align:top;">{m['name']}</td>
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
        standouts_html = ok_line("No standout sessions identified.")

    # ── Internal notes ─────────────────────────────────────────────────────────
    internal_html = ""
    for n in data["internal_notes"]:
        internal_html += f"""
        <div style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
          <div style="font-weight:700;font-size:13px;">{n['name']}</div>
          <div style="font-size:13px;color:#444;margin-top:2px;">{n['note']}</div>
        </div>"""
    if not internal_html:
        internal_html = ok_line("No internal notes yesterday &mdash; all systems ran smoothly!")

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

    def quality_section(title, color, items, empty_msg):
        html = sub_heading(title, color)
        if items:
            for item in items:
                html += f"""
                <div style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
                  <div style="font-weight:700;font-size:13px;">{item['name']}</div>
                  <div style="font-size:12px;color:#555;margin-top:2px;">{item['reason']}</div>
                </div>"""
        else:
            html += ok_line(empty_msg)
        return html

    qc_counts = [
        ("&#9888; Academic",   len(quality["academic"])),
        ("&#128680; Behavioral", len(quality["behavioral"])),
        ("&#128202; QC Issues",  len(quality["qc"])),
        ("&#128196; Missing LP", len(data["missing_lp"])),
    ]
    qc_stat_cards = ""
    for label, count in qc_counts:
        color = "#d4253a" if count > 0 else "#166534"
        qc_stat_cards += f"""
        <td style="width:25%;padding:0 6px 0 0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:12px 10px;text-align:center;">
            <div style="font-size:11px;color:#666;margin-bottom:4px;">{label}</div>
            <div style="font-size:26px;font-weight:700;color:{color};">{count}</div>
          </div>
        </td>"""

    # ─── Full HTML ─────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Morning Briefing &mdash; {data['center']} &mdash; {data['report_date']}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f0;font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;background:#fff;">

  <!-- HEADER -->
  <div style="background:#fff;border-bottom:1px solid #e0e0e0;padding:16px 28px;display:flex;align-items:center;justify-content:space-between;">
    <div style="font-size:18px;font-weight:700;color:#d4253a;letter-spacing:-0.5px;">M<span style="color:#f59e0b;">&#8743;</span>THNASIUM</div>
    <div style="font-size:12px;color:#555;text-align:right;">Morning Briefing<br><strong>{data['center']} Center</strong></div>
  </div>

  <!-- TITLE -->
  <div style="background:#fff;border-bottom:3px solid #d4253a;padding:18px 28px 14px;">
    <div style="font-size:22px;font-weight:700;color:#1a1a1a;">&#9728;&#65039; Morning Briefing</div>
    <div style="margin-top:6px;">
      <span style="display:inline-block;font-size:12px;font-weight:600;background:#fef2f2;color:#d4253a;border:1px solid #fcc;border-radius:4px;padding:2px 8px;">Center: {data['center']}</span>
    </div>
    <div style="font-size:13px;color:#666;margin-top:6px;">{data['report_date']}</div>
  </div>

  <div style="padding:24px 28px;">

    <!-- EXECUTIVE SUMMARY -->
    {section_start("&#127919; Executive Summary", left_color="#2563eb")}
      <p style="font-size:14px;line-height:1.7;color:#333;background:#fafafa;border-radius:6px;padding:16px 18px;margin:0;">
        {ai.get('executive_summary', 'Summary unavailable.')}
      </p>
    {section_end()}

    <!-- NEW ENROLLMENTS PLACEHOLDER -->
    {section_start("&#127881; New Enrollments", "Pulled from enrollment system &mdash; integration pending.", left_color="#888")}
      <div style="border:2px dashed #d0d0d0;border-radius:6px;padding:20px;text-align:center;color:#999;font-style:italic;font-size:13px;">
        Enrollment data will appear here once the enrollment system is connected.
      </div>
    {section_end()}

    <!-- ATTENDANCE -->
    {section_start("&#128101; Yesterday's Attendance", "Session snapshot with half-hour breakdown.")}
      {sub_heading("Session overview")}
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
        <tr>
          {stat_card("Total Sessions", data['total_sessions'])}
          {stat_card("Unique Students", data['unique_students'])}
        </tr>
      </table>
      {sub_heading("Seats occupied by half-hour")}
      <table width="100%" cellpadding="0" cellspacing="0">
        <thead>
          <tr style="background:#fafafa;">
            <th style="text-align:left;padding:6px 8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Time</th>
            <th style="text-align:left;padding:6px 8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Seats</th>
            <th style="text-align:left;padding:6px 8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Students</th>
          </tr>
        </thead>
        <tbody>{att_rows}</tbody>
      </table>
    {section_end()}

    <!-- ACADEMIC ACCOMPLISHMENTS -->
    {section_start("&#127891; Academic Accomplishments", "Mastery checks trigger a celebratory parent text &mdash; ensure all are documented in DWP.", left_color="#d97706")}
      {sub_heading("Yesterday's learning metrics")}
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
        <tr>
          {stat_card("&#128218; Pages Completed", data['total_pages'])}
          {stat_card("&#127941; Mastery Checks", data['total_mastery'])}
          {stat_card("&#11088; Avg Mathlete Score", f"{data['avg_score']}/3" if data['avg_score'] else "N/A")}
        </tr>
      </table>
      {sub_heading("Mastery achievements")}
      <p style="font-size:13px;font-weight:600;color:#444;margin:0 0 8px;">Students who completed mastery checks:</p>
      <table width="100%" cellpadding="0" cellspacing="0">
        <thead>
          <tr style="background:#fafafa;">
            <th style="text-align:left;padding:8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;width:35%;">Student</th>
            <th style="text-align:left;padding:8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Topics Mastered</th>
          </tr>
        </thead>
        <tbody>{mastery_rows}</tbody>
      </table>
      {sub_heading("Standout sessions")}
      {standouts_html}
    {section_end()}

    <!-- INTERNAL NOTES -->
    {section_start("&#128221; Internal Notes", "Instructor-flagged items for the Center Director's attention.", left_color="#6b7280")}
      {internal_html}
    {section_end()}

    <!-- INSTRUCTORS -->
    {section_start("&#128104;&#8205;&#127979; Instructors", "Workload breakdown for yesterday.", left_color="#2563eb")}
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
    {section_start("&#128269; Session Quality", "AI-detected flags from session notes.", left_color="#16a34a")}
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
        <tr>{qc_stat_cards}</tr>
      </table>
      {quality_section("&#9888; Academic Concerns",    "#d97706", quality["academic"],   "No academic concerns to report yesterday")}
      {quality_section("&#128680; Behavioral Concerns","#dc2626", quality["behavioral"], "No behavioral concerns to report yesterday")}
      {quality_section("&#128202; QC Issues",          "#2563eb", quality["qc"],         "No parent communication concerns to report yesterday")}
      {sub_heading("&#128196; Missing LP Assignments", "#16a34a")}
      {''.join(f'<div style="padding:6px 0;font-size:13px;font-weight:700;color:#dc2626;">{n}</div>' for n in data['missing_lp']) or ok_line("All sessions have LP tracking documented")}
    {section_end()}

  </div>
</div>
</body>
</html>"""

    return html


# ─── SEND FUNCTION ────────────────────────────────────────────────────────────

def send_report(data: dict, ai: dict, report_date: date = None) -> None:
    if report_date is None:
        report_date = date.today()

    recipients = [r.strip() for r in RECIPIENTS.split(",") if r.strip()]
    subject    = f"Morning Briefing \u2014 {CENTER_NAME} \u2014 {data['report_date']}"
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


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from parse import parse_report
    from generate import generate_all

    csv_path = sys.argv[1] if len(sys.argv) > 1 else "downloads/radius_today.csv"
    data = parse_report(csv_path)
    ai   = generate_all(data)
    send_report(data, ai)

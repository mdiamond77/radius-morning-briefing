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

# Logo embedded as base64 — no external URL needed, always displays in Gmail
LOGO_URL = "data:image/jpeg;base64,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"
# ──────────────────────────────────────────────────────────────────────────────


def _enrollment_section(e: dict) -> str:
    """Render the enrollment section HTML."""
    if not e:
        return '<div style="border:2px dashed #d0d0d0;border-radius:6px;padding:20px;text-align:center;color:#999;font-style:italic;font-size:13px;">Enrollment data unavailable.</div>'

    def fmt_date(d):
        if hasattr(d, "strftime"): return d.strftime("%-m/%-d")
        return str(d)

    def enroll_table(enrollments):
        if not enrollments:
            return '<p style="font-size:13px;font-style:italic;color:#999;margin:4px 0 10px;">None recorded.</p>'
        rows = ""
        for en in enrollments:
            typ = en.get("classification", "")
            color = "#1d4ed8" if typ == "new" else "#6d28d9"
            bg    = "#eff6ff" if typ == "new" else "#f5f3ff"
            label = "New" if typ == "new" else "Re-enroll"
            pill  = f'<span style="display:inline-block;font-size:10px;font-weight:700;background:{bg};color:{color};border-radius:3px;padding:1px 6px;margin-right:4px;">{label}</span>'
            rows += f'<tr><td style="padding:7px 8px;border-bottom:1px solid #f5f5f5;font-size:13px;font-weight:700;">{en["name"]}</td><td style="padding:7px 8px;border-bottom:1px solid #f5f5f5;font-size:13px;">{pill}</td><td style="padding:7px 8px;border-bottom:1px solid #f5f5f5;font-size:12px;color:#666;">{fmt_date(en["start"])}</td><td style="padding:7px 8px;border-bottom:1px solid #f5f5f5;font-size:12px;color:#666;">Gr.&nbsp;{en.get("grade","")}</td></tr>'
        return f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:10px;"><thead><tr style="background:#fafafa;"><th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.3px;">Student</th><th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.3px;">Type</th><th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.3px;">Start</th><th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.3px;">Grade</th></tr></thead><tbody>{rows}</tbody></table>'

    def type_block(title, color, this_m, last_m, this_w, m_label, lm_label, w_label, show_detail=True):
        """Render one enrollment type block. Detail only shown for current month/week."""
        if not this_m and not last_m and not this_w:
            return ""
        html  = f'<div style="margin-bottom:18px;">'
        html += f'<div style="font-size:13px;font-weight:500;color:{color};margin:14px 0 8px;padding-bottom:4px;border-bottom:2px solid {color};">{title}</div>'
        # Mini stat row — week / this month / last month
        html += '<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;"><tr>'
        for label, count in [(w_label, len(this_w)), (m_label, len(this_m)), (lm_label, len(last_m))]:
            html += f'<td style="padding:0 6px 0 0;"><div style="border:1px solid #e0e0e0;border-radius:6px;padding:10px 8px;text-align:center;"><div style="font-size:11px;color:#666;margin-bottom:4px;">{label}</div><div style="font-size:22px;font-weight:700;color:#1a1a1a;">{count}</div></div></td>'
        html += '</tr></table>'
        if show_detail:
            # This month detail only — week count shown in stat row above
            if this_m:
                html += f'<p style="font-size:12px;font-weight:700;color:#555;margin:8px 0 4px;">{m_label}</p>{enroll_table(this_m)}'
        html += '</div>'
        return html

    roster      = e.get("active_roster", "—")
    enrolled    = e.get("enrolled_count", "—")
    on_hold     = e.get("on_hold_count", "—")
    m_label     = e.get("month_label", "This month")
    lm_label    = e.get("last_month_label", "Last month")
    w_label     = e.get("week_label", "This week")
    report_date = e.get("report_date")

    this_m_all = e.get("this_month", [])
    last_m_all = e.get("last_month", [])
    this_w_all = e.get("this_week", [])

    # ── Top stat row ───────────────────────────────────────────────────────────
    def stat_td(label, val, sub=None):
        sub_html = f'<div style="font-size:10px;color:#999;margin-top:2px;">{sub}</div>' if sub else ""
        return f'<td style="padding:0 6px 0 0;"><div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px 10px;text-align:center;"><div style="font-size:12px;color:#666;margin-bottom:6px;">{label}</div><div style="font-size:28px;font-weight:700;color:#1a1a1a;">{val}</div>{sub_html}</div></td>'

    stat_row = '<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;"><tr>'
    on_hold_sub = f"plus {on_hold} on hold" if on_hold and on_hold != "—" and int(on_hold) > 0 else ""
    stat_row += stat_td("Active Roster", enrolled, on_hold_sub)
    stat_row += stat_td(f"New {m_label}", len(e.get("this_month_standard", [])))
    stat_row += stat_td(f"New {lm_label}", len(e.get("last_month_standard", [])))
    stat_row += stat_td(f"New {w_label}", len(e.get("this_week_standard", [])))
    stat_row += '</tr></table>'

    # ── Standard enrollments ───────────────────────────────────────────────────
    standard = type_block("Standard Enrollments", "#c8271e",
        e.get("this_month_standard", []), e.get("last_month_standard", []),
        e.get("this_week_standard", []), m_label, lm_label, w_label)

    # ── Private — only show if there are any TODAY ─────────────────────────────
    private_today = [en for en in e.get("this_week_private", [])
                     if report_date and hasattr(en.get("start"), "isoformat")
                     and en["start"] == report_date] if report_date else []
    private_today_all = [en for en in e.get("this_month_private", [])
                         if report_date and hasattr(en.get("start"), "isoformat")
                         and en["start"] == report_date] if report_date else []

    private = ""
    if private_today_all or e.get("this_month_private") or e.get("last_month_private"):
        # Show full block but only if there's data; detail only for today
        private = type_block("Private Enrollments", "#1d4ed8",
            e.get("this_month_private", []), e.get("last_month_private", []),
            e.get("this_week_private", []), m_label, lm_label, w_label)

    # ── Summer — only show if there are any ───────────────────────────────────
    summer = type_block("Summer Enrollments", "#d97706",
        e.get("this_month_summer", []), e.get("last_month_summer", []),
        e.get("this_week_summer", []), m_label, lm_label, w_label)

    # ── Plan changes — only show if any TODAY ─────────────────────────────────
    plans = e.get("plan_changes_this_month", [])
    plans_today = [p for p in plans
                   if report_date and hasattr(p.get("start"), "isoformat")
                   and p["start"] == report_date] if report_date else []

    plan_section = ""
    if plans_today:
        plan_rows = "".join(
            f'<tr><td style="padding:6px 8px;border-bottom:1px solid #f5f5f5;font-size:13px;">{p["name"]}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #f5f5f5;font-size:12px;color:#666;">{fmt_date(p["start"])}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #f5f5f5;font-size:12px;color:#666;">{p.get("type","")}</td></tr>'
            for p in plans_today
        )
        plan_section = f"""
        <div style="margin-bottom:18px;">
          <div style="font-size:13px;font-weight:500;color:#6b7280;margin:14px 0 8px;padding-bottom:4px;border-bottom:2px solid #e0e0e0;">Plan Changes Today (not counted)</div>
          <table width="100%" cellpadding="0" cellspacing="0" style="opacity:0.8;">
            <thead><tr style="background:#fafafa;">
              <th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.3px;">Student</th>
              <th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.3px;">Date</th>
              <th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.3px;">Plan</th>
            </tr></thead>
            <tbody>{plan_rows}</tbody>
          </table>
        </div>"""

    return stat_row + standard + private + summer + plan_section
    """Render the enrollment section HTML."""
    if not e:
        return '<div style="border:2px dashed #d0d0d0;border-radius:6px;padding:20px;text-align:center;color:#999;font-style:italic;font-size:13px;">Enrollment data unavailable.</div>'

    def fmt_date(d):
        if hasattr(d, "strftime"): return d.strftime("%-m/%-d")
        return str(d)

    def enroll_table(enrollments):
        if not enrollments:
            return '<p style="font-size:13px;font-style:italic;color:#999;margin:4px 0 10px;">None recorded.</p>'
        rows = ""
        for en in enrollments:
            typ = en.get("classification", "")
            color = "#1d4ed8" if typ == "new" else "#6d28d9"
            bg    = "#eff6ff" if typ == "new" else "#f5f3ff"
            label = "New" if typ == "new" else "Re-enroll"
            typ_html = f'<span style="display:inline-block;font-size:10px;font-weight:700;background:{bg};color:{color};border-radius:3px;padding:1px 6px;margin-right:5px;">{label}</span>'
            rows += f'<tr><td style="padding:7px 8px;border-bottom:1px solid #f5f5f5;font-size:13px;font-weight:700;">{en["name"]}</td><td style="padding:7px 8px;border-bottom:1px solid #f5f5f5;font-size:13px;">{typ_html}</td><td style="padding:7px 8px;border-bottom:1px solid #f5f5f5;font-size:12px;color:#666;">{fmt_date(en["start"])}</td><td style="padding:7px 8px;border-bottom:1px solid #f5f5f5;font-size:12px;color:#666;">Gr.&nbsp;{en.get("grade","")}</td></tr>'
        return f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:10px;"><thead><tr style="background:#fafafa;"><th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;">Student</th><th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;">Type</th><th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;">Start</th><th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;">Grade</th></tr></thead><tbody>{rows}</tbody></table>'

    def type_block(title, color, this_m, last_m, this_w, m_label, lm_label, w_label):
        """Render one enrollment type block (standard / private / summer)."""
        # Only render if there's any data across all windows
        if not this_m and not last_m and not this_w:
            return ""
        html = f'<div style="margin-bottom:18px;">'
        html += f'<div style="font-size:13px;font-weight:700;color:{color};margin:14px 0 8px;padding-bottom:4px;border-bottom:2px solid {color};">{title}</div>'
        # Stat mini-row
        html += f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;"><tr>'
        for label, count in [(w_label, len(this_w)), (m_label, len(this_m)), (lm_label, len(last_m))]:
            html += f'<td style="padding:0 6px 0 0;"><div style="border:1px solid #e0e0e0;border-radius:6px;padding:10px 8px;text-align:center;"><div style="font-size:11px;color:#666;margin-bottom:4px;">{label}</div><div style="font-size:22px;font-weight:700;color:#1a1a1a;">{count}</div></div></td>'
        html += '</tr></table>'
        # Detail tables
        if this_w:
            html += f'<p style="font-size:12px;font-weight:700;color:#555;margin:8px 0 4px;">{w_label} detail</p>{enroll_table(this_w)}'
        if this_m:
            html += f'<p style="font-size:12px;font-weight:700;color:#555;margin:8px 0 4px;">{m_label} detail</p>{enroll_table(this_m)}'
        if last_m:
            html += f'<p style="font-size:12px;font-weight:700;color:#555;margin:8px 0 4px;">{lm_label} detail</p>{enroll_table(last_m)}'
        html += '</div>'
        return html

    roster  = e.get("active_roster", "—")
    m_label = e.get("month_label", "This month")
    lm_label= e.get("last_month_label", "Last month")
    w_label = e.get("week_label", "This week")

    # Top stat boxes — totals across all types
    this_m_all = e.get("this_month", [])
    last_m_all = e.get("last_month", [])
    this_w_all = e.get("this_week", [])

    stat_row = f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
      <tr>
        <td style="padding:0 6px 0 0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px 10px;text-align:center;">
            <div style="font-size:12px;color:#666;margin-bottom:6px;">Active Roster</div>
            <div style="font-size:28px;font-weight:700;color:#1a1a1a;">{roster}</div>
          </div>
        </td>
        <td style="padding:0 6px 0 0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px 10px;text-align:center;">
            <div style="font-size:12px;color:#666;margin-bottom:6px;">{m_label}</div>
            <div style="font-size:28px;font-weight:700;color:#1a1a1a;">{len(this_m_all)}</div>
          </div>
        </td>
        <td style="padding:0 6px 0 0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px 10px;text-align:center;">
            <div style="font-size:12px;color:#666;margin-bottom:6px;">{lm_label}</div>
            <div style="font-size:28px;font-weight:700;color:#1a1a1a;">{len(last_m_all)}</div>
          </div>
        </td>
        <td style="padding:0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px 10px;text-align:center;">
            <div style="font-size:12px;color:#666;margin-bottom:6px;">{w_label}</div>
            <div style="font-size:28px;font-weight:700;color:#1a1a1a;">{len(this_w_all)}</div>
          </div>
        </td>
      </tr>
    </table>"""

    # Type breakdowns
    standard = type_block("Standard Enrollments", "#c8271e",
        e.get("this_month_standard", []), e.get("last_month_standard", []), e.get("this_week_standard", []),
        m_label, lm_label, w_label)

    private = type_block("Private Enrollments", "#1d4ed8",
        e.get("this_month_private", []), e.get("last_month_private", []), e.get("this_week_private", []),
        m_label, lm_label, w_label)

    summer = type_block("Summer Enrollments", "#d97706",
        e.get("this_month_summer", []), e.get("last_month_summer", []), e.get("this_week_summer", []),
        m_label, lm_label, w_label)

    # Plan changes
    plans = e.get("plan_changes_this_month", [])
    if plans:
        plan_rows = "".join(
            f'<tr><td style="padding:6px 8px;border-bottom:1px solid #f5f5f5;font-size:13px;">{p["name"]}</td><td style="padding:6px 8px;border-bottom:1px solid #f5f5f5;font-size:12px;color:#666;">{fmt_date(p["start"])}</td><td style="padding:6px 8px;border-bottom:1px solid #f5f5f5;font-size:12px;color:#666;">{p.get("type","")}</td></tr>'
            for p in plans
        )
        plan_section = f"""
        <div style="margin-bottom:18px;">
          <div style="font-size:13px;font-weight:700;color:#6b7280;margin:14px 0 8px;padding-bottom:4px;border-bottom:2px solid #e0e0e0;">Plan Changes (not counted)</div>
          <table width="100%" cellpadding="0" cellspacing="0" style="opacity:0.75;">
            <thead><tr style="background:#fafafa;">
              <th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;">Student</th>
              <th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;">Date</th>
              <th style="text-align:left;padding:6px 8px;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;">Plan</th>
            </tr></thead>
            <tbody>{plan_rows}</tbody>
          </table>
        </div>"""
    else:
        plan_section = ""

    return stat_row + standard + private + summer + plan_section


def render_email(data: dict, ai: dict, enrollment_data: dict = None) -> str:
    enrollment_data = enrollment_data or {}

    # ── Helpers ───────────────────────────────────────────────────────────────
    def stat_box(label, value, sub=None):
        sub_html = f'<div style="font-size:10px;color:#999;margin-top:3px;">{sub}</div>' if sub else ""
        return f"""
        <td style="padding:0 6px 0 0;">
          <div style="border:1px solid #e0e0e0;border-radius:6px;padding:14px 10px;text-align:center;">
            <div style="font-size:12px;color:#666;margin-bottom:6px;">{label}</div>
            <div style="font-size:28px;font-weight:700;color:#1a1a1a;line-height:1;">{value}</div>
            {sub_html}
          </div>
        </td>"""

    private_count = data.get("private_sessions", 0)
    private_note  = f"inc. {private_count} private" if private_count else None

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
          <td style="padding:8px 8px 2px;font-size:13px;color:#555;white-space:nowrap;">
            {b['label']}{peak_tag}
          </td>
          <td style="padding:8px 8px 2px;width:120px;">
            <div style="background:#f0f0f0;border-radius:3px;height:12px;overflow:hidden;">
              <div style="background:#c8271e;opacity:{bar_opacity};height:100%;width:{pct}%;border-radius:3px;"></div>
            </div>
          </td>
          <td style="padding:8px 8px 2px;font-size:13px;font-weight:700;text-align:center;">{b['count']}</td>
          <td style="padding:8px 8px 2px;font-size:13px;font-weight:700;text-align:center;">{b.get('instructors', '—')}</td>
          <td style="padding:8px 8px 2px;font-size:13px;font-weight:700;text-align:center;color:{ratio_color};">{ratio_str}</td>
        </tr>
        <tr>
          <td colspan="5" style="padding:0 8px 8px 8px;font-size:11px;color:#999;border-bottom:1px solid #f5f5f5;">
            {', '.join(b['students'])}
          </td>
        </tr>"""

    # ── Below 3.0 Mathlete score ───────────────────────────────────────────────
    below_mathlete = [
        s for s in data["sessions"]
        if s["score"] is not None and s["score"] < 3.0
    ]
    if below_mathlete:
        below_rows = "".join(
            f'<tr>'
            f'<td style="padding:8px;border-bottom:1px solid #f0f0f0;font-weight:700;font-size:13px;">{s["name"]}</td>'
            f'<td style="padding:8px;border-bottom:1px solid #f0f0f0;font-size:13px;">'
            f'<span style="display:inline-block;background:#fef9c3;color:#713f12;border:1px solid #fde047;border-radius:3px;padding:1px 6px;font-size:11px;font-weight:600;">{s["score"]}/3</span>'
            f'</td>'
            f'</tr>'
            for s in sorted(below_mathlete, key=lambda x: x["score"])
        )
        below_mathlete_html = f"""
        {subh("Below 3.0 Mathlete score", color="#854F0B")}
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
          <thead><tr style="background:#fafafa;">
            <th style="text-align:left;padding:6px 8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Student</th>
            <th style="text-align:left;padding:6px 8px;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;">Score</th>
          </tr></thead>
          <tbody>{below_rows}</tbody>
        </table>"""
    else:
        below_mathlete_html = ""

    # ── Assessment section ─────────────────────────────────────────────────────
    def assessment_cell(names):
        if not names:
            return '<span style="font-size:12px;font-style:italic;color:#999;">None today</span>'
        return "".join(
            f'<div style="font-size:13px;padding:2px 0;color:#1a1a1a;">{n}</div>'
            for n in names
        )

    assessments = data.get("assessments", {})
    any_assessments = any(assessments.get(k) for k in assessments)
    if any_assessments:
        assessment_html = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8e8e8;border-radius:8px;border-collapse:separate;border-spacing:0;overflow:hidden;">
          <thead>
            <tr style="background:#fafafa;">
              <th style="width:130px;padding:8px 12px;text-align:left;font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.3px;border-bottom:1px solid #e8e8e8;border-right:1px solid #e8e8e8;"></th>
              <th style="padding:8px 12px;text-align:left;font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.3px;border-bottom:1px solid #e8e8e8;border-right:1px solid #e8e8e8;">In progress</th>
              <th style="padding:8px 12px;text-align:left;font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.3px;border-bottom:1px solid #e8e8e8;">Completed</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="padding:10px 12px;font-size:12px;font-weight:600;color:#1a1a1a;background:#fafafa;border-right:1px solid #e8e8e8;border-bottom:1px solid #e8e8e8;vertical-align:top;">Pre</td>
              <td style="padding:10px 12px;border-right:1px solid #e8e8e8;border-bottom:1px solid #e8e8e8;vertical-align:top;">{assessment_cell(assessments.get("pre_in_progress", []))}</td>
              <td style="padding:10px 12px;border-bottom:1px solid #e8e8e8;vertical-align:top;">{assessment_cell(assessments.get("pre_completed", []))}</td>
            </tr>
            <tr>
              <td style="padding:10px 12px;font-size:12px;font-weight:600;color:#1a1a1a;background:#fafafa;border-right:1px solid #e8e8e8;border-bottom:1px solid #e8e8e8;vertical-align:top;">Post</td>
              <td style="padding:10px 12px;border-right:1px solid #e8e8e8;border-bottom:1px solid #e8e8e8;vertical-align:top;">{assessment_cell(assessments.get("post_in_progress", []))}</td>
              <td style="padding:10px 12px;border-bottom:1px solid #e8e8e8;vertical-align:top;">{assessment_cell(assessments.get("post_completed", []))}</td>
            </tr>
            <tr>
              <td style="padding:10px 12px;font-size:12px;font-weight:600;color:#1a1a1a;background:#fafafa;border-right:1px solid #e8e8e8;vertical-align:top;">Progress Check</td>
              <td style="padding:10px 12px;border-right:1px solid #e8e8e8;vertical-align:top;">{assessment_cell(assessments.get("progress_in_progress", []))}</td>
              <td style="padding:10px 12px;vertical-align:top;">{assessment_cell(assessments.get("progress_completed", []))}</td>
            </tr>
          </tbody>
        </table>"""
        assessment_section = f"""
    {section("Assessments", "Students with active or completed assessments today")}
      {assessment_html}
    {section_end()}"""
    else:
        assessment_section = ""
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
        cd = i.get("is_center_director", False)
        name_html = f'{i["name"]} <span style="font-size:11px;font-weight:400;color:#888;font-style:italic;">(CD — excluded from ratios)</span>' if cd else i["name"]
        instructor_rows += f"""
        <tr style="{'opacity:0.7;' if cd else ''}">
          <td style="padding:8px;border-bottom:1px solid #f0f0f0;font-weight:700;font-size:13px;">{name_html}</td>
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

  <!-- RED HEADER — single bar with logo, title, and date -->
  <div style="background:#c8271e;padding:20px 28px 16px;display:flex;align-items:center;justify-content:space-between;">
    <img src="{LOGO_URL}" alt="Mathnasium" height="52" style="display:block;filter:brightness(0) invert(1);">
    <div style="text-align:right;color:#fff;">
      <div style="font-size:20px;font-weight:500;line-height:1.2;">Daily Summary Report &mdash; {data['center']}</div>
      <div style="font-size:12px;opacity:0.85;margin-top:4px;">{data['report_date']}</div>
    </div>
  </div>

  <div style="padding:24px 28px;">

    <!-- DAILY SUMMARY (AI) -->
    {section("Daily Summary", "AI-generated overview of today&rsquo;s sessions")}
      <p style="font-size:13px;color:#555;margin-bottom:6px;font-style:italic;">&#9679; AI-generated</p>
      <p style="font-size:14px;line-height:1.75;color:#333;background:#fafafa;border-radius:6px;padding:16px 18px;margin:0;">
        {ai.get('executive_summary', 'Summary unavailable.')}
      </p>
    {section_end()}

    <!-- ENROLLMENTS -->
    {section("Enrollments", "New and re-enrollments only &mdash; plan changes excluded")}
      {_enrollment_section(enrollment_data)}
    {section_end()}

    <!-- ATTENDANCE -->
    {section("Attendance", "Half-hour occupancy with student-to-instructor ratio")}
      {subh("Session overview")}
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
        <tr>
          {stat_box("Total Sessions", data['total_sessions'], private_note)}
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
          </tr>
        </thead>
        <tbody>{att_rows}</tbody>
      </table>
    {section_end()}

    <!-- ASSESSMENTS -->
    {assessment_section}

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
      {below_mathlete_html}
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
      {f'<div style="margin-top:8px;font-size:12px;font-weight:600;color:#854F0B;">Likely study/homework related (no LP expected):</div>' + ''.join(f'<div style="padding:3px 0;font-size:13px;color:#854F0B;">{n}</div>' for n in data.get('missing_lp_study', [])) if data.get('missing_lp_study') else ''}
    {section_end()}

  </div>
</div>
</body>
</html>"""


def send_report(data: dict, ai: dict, enrollment_data: dict = None, report_date: date = None) -> None:
    if report_date is None:
        report_date = date.today()

    recipients = [r.strip() for r in RECIPIENTS.split(",") if r.strip()]
    subject    = f"Daily Summary \u2014 {CENTER_NAME} \u2014 {data['report_date']}"
    html_body  = render_email(data, ai, enrollment_data or {})

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
    from parse_enrollment import parse_enrollment_report
    from generate import generate_all
    dwp_path        = sys.argv[1] if len(sys.argv) > 1 else "downloads/radius_today.xlsx"
    enrollment_path = sys.argv[2] if len(sys.argv) > 2 else "downloads/enrollment_today.xlsx"
    center          = sys.argv[3] if len(sys.argv) > 3 else "Teaneck"
    data            = parse_report(dwp_path)
    enrollment_data = parse_enrollment_report(enrollment_path, center)
    ai              = generate_all(data)
    send_report(data, ai, enrollment_data)

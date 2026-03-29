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

# Logo embedded as base64 PNG (white, transparent bg) — always displays in Gmail
LOGO_URL = "data:image/png;base64,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"
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
        # Show first instructor name only (may be comma-separated if team-taught)
        instructor = (n.get("instructor") or "").split(",")[0].strip()
        instructor_html = f'<span style="font-size:11px;color:#888;font-style:italic;margin-left:6px;">— {instructor}</span>' if instructor else ""
        internal_html += f"""
        <div style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
          <div style="font-weight:700;font-size:13px;">{n['name']}{instructor_html}</div>
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
    <img src="{LOGO_URL}" alt="Mathnasium" height="52" style="display:block;">
    <div style="text-align:right;color:#fff;">
      <div style="font-size:20px;font-weight:500;line-height:1.2;">Daily Summary Report &mdash; {data['center']}</div>
      <div style="font-size:12px;opacity:0.85;margin-top:4px;">{data['report_date']}</div>
    </div>
  </div>

  <div style="padding:24px 28px;">

    <!-- DAILY SUMMARY (AI) -->
    {section("Daily Summary", "AI-generated overview of today&rsquo;s sessions")}
      <p style="font-size:13px;color:#555;margin-bottom:10px;font-style:italic;">&#9679; AI-generated</p>
      <div style="background:#fafafa;border-radius:6px;padding:14px 18px;">
        {"".join(
            f'<div style="display:flex;gap:10px;padding:4px 0;font-size:14px;line-height:1.6;color:#333;"><span style="color:#c8271e;font-weight:700;flex-shrink:0;">–</span><span>{line.lstrip("-–—").strip()}</span></div>'
            for line in ai.get("executive_summary", "Summary unavailable.").split("\n")
            if line.strip() and line.strip() not in ("-", "–", "—")
        )}
      </div>
    {section_end()}

    <!-- INTERNAL NOTES -->
    {section("Internal Notes", "Instructor-flagged items for the Center Director")}
      {internal_html}
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

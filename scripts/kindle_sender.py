"""Send daily briefing to Kindle device via email attachment (Send-to-Kindle)."""

import os
import re
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

KINDLE_TO = "kenimania1_Kacx5P@kindle.com"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(s: str) -> str:
    """Convert inline markdown (links, bold) to HTML."""
    s = re.sub(
        r'\[([^\]]*)\]\(([^)]*)\)',
        lambda m: f'<a href="{m.group(2)}">{_esc(m.group(1))}</a>',
        s,
    )
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    return s


def _build_html(briefing_md: str, date_str: str) -> str:
    """Convert briefing markdown to Kindle-friendly HTML."""
    text = re.sub(r"^---\n.*?\n---\n", "", briefing_md, flags=re.DOTALL).strip()

    lines = text.split("\n")
    parts: list[str] = []
    buf: list[str] = []
    in_table = False
    table_rows: list[list[str]] = []

    def flush_buf():
        if buf:
            parts.append("<p>" + "<br/>".join(buf) + "</p>")
            buf.clear()

    def flush_table():
        nonlocal in_table
        if table_rows:
            rows_html = []
            for cells in table_rows:
                tds = "".join(f"<td>{_esc(c)}</td>" for c in cells)
                rows_html.append(f"<tr>{tds}</tr>")
            parts.append("<table>" + "".join(rows_html) + "</table>")
            table_rows.clear()
        in_table = False

    for line in lines:
        s = line.strip()

        if not s:
            flush_buf()
            if in_table:
                flush_table()
            continue

        if re.match(r"^# (?!#)", s):
            flush_buf()
            parts.append(f"<h1>{_esc(s[2:])}</h1>")

        elif re.match(r"^## (?!#)", s):
            flush_buf()
            if in_table:
                flush_table()
            parts.append(f"<h2>{_esc(s[3:])}</h2>")

        elif re.match(r"^### ", s):
            flush_buf()
            parts.append(f"<h3>{_inline(s[4:])}</h3>")

        elif re.match(r"^---", s) or s.startswith("*Generated"):
            flush_buf()
            if in_table:
                flush_table()
            if not s.startswith("*"):
                parts.append("<hr/>")

        elif re.match(r"^\|[-| ]+\|$", s):
            in_table = True

        elif s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.split("|")[1:-1]]
            if cells and cells[0] not in ("EN", ""):
                table_rows.append(cells)
                in_table = True

        else:
            if in_table:
                flush_table()
            buf.append(_inline(s))

    flush_buf()
    if in_table:
        flush_table()

    body = "\n".join(parts)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<title>Daily Briefing {date_str}</title>
<style>
body {{
  font-family: Georgia, "Malgun Gothic", serif;
  font-size: 1em;
  line-height: 1.8;
  margin: 1.5em;
  color: #111;
}}
h1 {{
  font-size: 1.5em;
  border-bottom: 2px solid #222;
  padding-bottom: 0.3em;
  margin-bottom: 0.8em;
}}
h2 {{
  font-size: 1.2em;
  color: #1a1a6e;
  margin-top: 2em;
  border-left: 4px solid #1a1a6e;
  padding-left: 0.5em;
}}
h3 {{
  font-size: 1em;
  font-weight: bold;
  margin-top: 1.5em;
  color: #222;
}}
p {{
  margin: 0.5em 0;
}}
hr {{
  border: none;
  border-top: 1px solid #bbb;
  margin: 1.5em 0;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 0.8em 0;
  font-size: 0.95em;
}}
td {{
  padding: 0.4em 0.6em;
  border: 1px solid #ccc;
  vertical-align: top;
  width: 50%;
}}
a {{
  color: #0645ad;
  text-decoration: none;
}}
b {{
  color: #333;
}}
</style>
</head>
<body>
{body}
</body>
</html>"""


def send_to_kindle(briefing_md: str, date_str: str) -> bool:
    """Send briefing as HTML attachment to Kindle via SMTP.

    Required env vars:
      SMTP_USER      — sender email (must be in Amazon Approved Senders list)
      SMTP_PASSWORD  — SMTP password / Gmail App Password

    Optional env vars:
      SMTP_HOST      — SMTP server (default: smtp.gmail.com)
      SMTP_PORT      — SMTP port   (default: 587)
    """
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASSWORD")

    if not smtp_user or not smtp_pass:
        print("  Skipped (SMTP_USER / SMTP_PASSWORD not set)")
        return False

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    html_content = _build_html(briefing_md, date_str)
    filename = f"{date_str}-daily-briefing.html"

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = KINDLE_TO
    msg["Subject"] = f"Daily Briefing {date_str}"

    msg.attach(MIMEText(f"Daily Briefing {date_str}", "plain", "utf-8"))

    attachment = MIMEBase("text", "html", charset="utf-8")
    attachment.set_payload(html_content.encode("utf-8"))
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, KINDLE_TO, msg.as_string())
        print(f"  Kindle email sent → {KINDLE_TO} ({filename})")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to send Kindle email: {exc}")
        return False

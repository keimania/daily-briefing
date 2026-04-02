"""Send daily briefing summary to Telegram via Bot API."""

import os
import re
import urllib.request
import json
import time


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_telegram_summary(briefing_md: str, date_str: str) -> str:
    """Extract title, link, and EN summary only for a compact Telegram message."""
    # Strip YAML frontmatter
    text = re.sub(r"^---\n.*?\n---\n", "", briefing_md, flags=re.DOTALL).strip()

    lines = text.split("\n")
    result = []
    current_section = ""
    current_article = {}
    in_en_summary = False

    def flush_article():
        if current_article.get("title"):
            title = _escape_html(current_article["title"])
            url = current_article.get("url", "")
            summary = _escape_html(current_article.get("summary", "").strip())
            if url:
                result.append(f"\n\u2022 <a href=\"{url}\">{title}</a>")
            else:
                result.append(f"\n\u2022 <b>{title}</b>")
            if summary:
                result.append(f"  {summary}")

    for line in lines:
        stripped = line.strip()

        # ## Section header
        if stripped.startswith("## ") and not stripped.startswith("### "):
            flush_article()
            current_article = {}
            in_en_summary = False
            section = stripped[3:]
            if "Key Takeaways" in section or "핵심" in section:
                current_section = "takeaways"
                result.append(f"\n{'─' * 25}")
                result.append(f"\U0001F4CB <b>Key Takeaways</b>")
            else:
                current_section = section
                result.append(f"\n{'─' * 25}")
                emoji = "\U0001F4C8" if "Exchange" in section or "Finance" in section else "\U0001F916"
                result.append(f"{emoji} <b>{_escape_html(section)}</b>")

        # ### Article header
        elif stripped.startswith("### "):
            flush_article()
            current_article = {}
            in_en_summary = False
            content = stripped[4:]
            link_match = re.match(r"\d+\.\s*\[(.+?)\]\((.+?)\)", content)
            if link_match:
                current_article["title"] = link_match.group(1)
                current_article["url"] = link_match.group(2)
            else:
                current_article["title"] = content

        # **Summary (EN):** inline or next line
        elif stripped.startswith("**Summary (EN):**"):
            remaining = stripped.replace("**Summary (EN):**", "").strip()
            current_article["summary"] = remaining
            in_en_summary = True

        # **요약 (KR):** -> stop collecting EN summary
        elif stripped.startswith("**\uc694\uc57d (KR):**"):
            in_en_summary = False

        # **Source:** / **Tags:** -> skip, stop EN summary
        elif stripped.startswith("**Source:**") or stripped.startswith("**Tags:**"):
            in_en_summary = False

        # Table rows (Key Takeaways) - EN only
        elif current_section == "takeaways" and stripped.startswith("|") and not stripped.startswith("|---"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) >= 1 and cells[0] != "EN":
                result.append(f"  \u2022 {_escape_html(cells[0])}")

        # Continuation of EN summary
        elif in_en_summary and stripped and not stripped.startswith("**"):
            current_article["summary"] = current_article.get("summary", "") + " " + stripped

        # Skip everything else (KR summary, tags, blank lines, etc.)

    flush_article()

    header = f"\U0001F4F0 <b>Daily Briefing \u2014 {date_str}</b>"
    body = "\n".join(result).strip()
    return f"{header}\n\n{body}"


def send_to_telegram(briefing_md: str, date_str: str) -> bool:
    """Send compact briefing to Telegram chat via Bot API.

    Requires environment variables:
    - TELEGRAM_BOT_TOKEN: Bot token from @BotFather
    - TELEGRAM_CHAT_ID: Target chat/channel ID
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("[WARN] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Skipping Telegram.")
        return False

    message = _build_telegram_summary(briefing_md, date_str)

    # Split into chunks under Telegram's 4096 char limit
    max_len = 3500
    chunks = []
    if len(message) <= max_len:
        chunks = [message]
    else:
        # Split at article boundaries (bullet points)
        parts = re.split(r"(?=\n\u2022 )", message)
        current = ""
        for part in parts:
            if len(current) + len(part) > max_len and current:
                chunks.append(current.strip())
                current = part
            else:
                current += part
        if current.strip():
            chunks.append(current.strip())

    success = True
    for i, msg in enumerate(chunks):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                if not result.get("ok"):
                    print(f"[ERROR] Telegram API error (chunk {i+1}): {result}")
                    success = False
                else:
                    print(f"  Telegram message sent (chunk {i+1}/{len(chunks)})")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"[ERROR] Telegram API HTTP {e.code} (chunk {i+1}): {body}")
            # Retry without HTML parse mode as fallback
            payload_plain = json.dumps({
                "chat_id": chat_id,
                "text": msg.replace("<b>", "").replace("</b>", "").replace("<a href=\"", "").replace("\">", " - ").replace("</a>", ""),
                "disable_web_page_preview": False,
            }).encode("utf-8")
            req_plain = urllib.request.Request(url, data=payload_plain, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req_plain) as resp2:
                    print(f"  Telegram message sent as plain text (chunk {i+1}/{len(chunks)})")
            except Exception as e2:
                print(f"[ERROR] Fallback also failed (chunk {i+1}): {e2}")
                success = False
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram message (chunk {i+1}): {e}")
            success = False

        if i < len(chunks) - 1:
            time.sleep(0.5)

    return success

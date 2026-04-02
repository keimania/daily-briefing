"""Send daily briefing to Telegram via Bot API using HTML formatting."""

import os
import re
import urllib.request
import json
import time


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md_to_telegram_html(briefing_md: str) -> str:
    """Convert Obsidian markdown briefing to Telegram-compatible HTML."""
    # Strip YAML frontmatter
    text = re.sub(r"^---\n.*?\n---\n", "", briefing_md, flags=re.DOTALL).strip()

    lines = text.split("\n")
    result = []

    for line in lines:
        stripped = line.strip()

        # # Title -> bold title with emoji
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = _escape_html(stripped[2:])
            result.append(f"\U0001F4F0 <b>{title}</b>")

        # ## Section header
        elif stripped.startswith("## "):
            header = _escape_html(stripped[3:])
            result.append(f"\n{'=' * 30}")
            result.append(f"\U0001F4CC <b>{header}</b>")
            result.append("=" * 30)

        # ### Article header: [Title](link)
        elif stripped.startswith("### "):
            content = stripped[4:]
            # Extract [title](url)
            link_match = re.match(r"\d+\.\s*\[(.+?)\]\((.+?)\)", content)
            if link_match:
                title = _escape_html(link_match.group(1))
                url = link_match.group(2)
                result.append(f"\n\U0001F539 <b>{title}</b>")
                result.append(f"\U0001F517 {url}")
            else:
                result.append(f"\n\U0001F539 <b>{_escape_html(content)}</b>")

        # **Source:** ...
        elif stripped.startswith("**Source:**"):
            source = _escape_html(stripped.replace("**Source:**", "").strip())
            result.append(f"\U0001F4F1 {source}")

        # **Summary (EN):**
        elif stripped.startswith("**Summary (EN):**"):
            remaining = stripped.replace("**Summary (EN):**", "").strip()
            if remaining:
                result.append(f"\n\U0001F1EC\U0001F1E7 <b>EN:</b> {_escape_html(remaining)}")
            else:
                result.append(f"\n\U0001F1EC\U0001F1E7 <b>EN:</b>")

        # **요약 (KR):**
        elif stripped.startswith("**\uc694\uc57d (KR):**"):
            remaining = stripped.replace("**\uc694\uc57d (KR):**", "").strip()
            if remaining:
                result.append(f"\n\U0001F1F0\U0001F1F7 <b>KR:</b> {_escape_html(remaining)}")
            else:
                result.append(f"\n\U0001F1F0\U0001F1F7 <b>KR:</b>")

        # **Tags:** ...
        elif stripped.startswith("**Tags:**"):
            tags = stripped.replace("**Tags:**", "").strip()
            result.append(f"\U0001F3F7 {_escape_html(tags)}")

        # Table rows (Key Takeaways)
        elif stripped.startswith("|") and not stripped.startswith("|---"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) == 2 and cells[0] != "EN":
                en_text = _escape_html(cells[0])
                kr_text = _escape_html(cells[1])
                result.append(f"\n\u2022 {en_text}")
                result.append(f"  \u21B3 {kr_text}")

        # Table header (skip)
        elif stripped.startswith("|---"):
            continue

        # Table header row
        elif stripped.startswith("| EN"):
            continue

        # Horizontal rule / generator note
        elif stripped.startswith("---") or stripped.startswith("*Generated"):
            if stripped.startswith("*Generated"):
                result.append(f"\n{'_' * 30}")
                result.append(_escape_html(stripped.strip("*")))
            continue

        # Regular text (summary continuation lines)
        elif stripped:
            result.append(_escape_html(stripped))

        # Blank lines -> keep one
        else:
            if result and result[-1] != "":
                result.append("")

    return "\n".join(result).strip()


def _split_message(text: str, max_len: int = 4000) -> list[str]:
    """Split a long message into chunks, breaking at double newlines."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    # Split at section boundaries (=== lines)
    sections = re.split(r"(?=\n={20,}\n)", text)
    current = ""

    for section in sections:
        if len(current) + len(section) > max_len:
            if current:
                chunks.append(current.strip())
            # If single section is too long, split at article boundaries
            if len(section) > max_len:
                parts = re.split(r"(?=\n\U0001F539 )", section)
                sub = ""
                for part in parts:
                    if len(sub) + len(part) > max_len:
                        if sub:
                            chunks.append(sub.strip())
                        sub = part
                    else:
                        sub += part
                current = sub
            else:
                current = section
        else:
            current += section

    if current.strip():
        chunks.append(current.strip())

    return chunks


def send_to_telegram(briefing_md: str, date_str: str) -> bool:
    """Send briefing to Telegram chat via Bot API.

    Requires environment variables:
    - TELEGRAM_BOT_TOKEN: Bot token from @BotFather
    - TELEGRAM_CHAT_ID: Target chat/channel ID
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("[WARN] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Skipping Telegram.")
        return False

    html_text = _md_to_telegram_html(briefing_md)
    messages = _split_message(html_text)

    success = True
    for i, msg in enumerate(messages):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
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
                    print(f"  Telegram message sent (chunk {i+1}/{len(messages)})")
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram message (chunk {i+1}): {e}")
            success = False

        # Rate limit: slight delay between messages
        if i < len(messages) - 1:
            time.sleep(0.5)

    return success

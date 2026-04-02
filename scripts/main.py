#!/usr/bin/env python3
"""Daily Briefing Generator - Main entry point.

Collects RSS news, summarizes with Gemini API, and generates Obsidian-compatible md files.
Optionally sends the briefing to Telegram.
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from rss_sources import ALL_FEEDS
from collect_news import collect_all
from summarizer import generate_briefing
from telegram_sender import send_to_telegram


def get_kst_date() -> str:
    """Get current date in KST (UTC+9)."""
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime("%Y-%m-%d")


def get_output_path(date_str: str, base_dir: str | None = None) -> Path:
    """Generate output file path: briefings/YYYY/MM/YYYY-MM-DD-daily-briefing.md"""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
    else:
        base_dir = Path(base_dir)

    year, month, _ = date_str.split("-")
    output_dir = base_dir / "briefings" / year / month
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{date_str}-daily-briefing.md"


def main():
    print("=" * 60)
    print("Daily Briefing Generator")
    print("=" * 60)

    date_str = get_kst_date()
    print(f"\nDate (KST): {date_str}")

    # Step 1: Collect news
    print("\n[1/4] Collecting news from RSS feeds...")
    articles = collect_all(ALL_FEEDS, hours_back=28)

    total = sum(len(v) for v in articles.values())
    print(f"\n  Total unique articles collected: {total}")
    print(f"    - Exchange & Finance: {len(articles['exchange_finance'])}")
    print(f"    - AI & Tech: {len(articles['ai_tech'])}")

    if total == 0:
        print("\n[WARN] No articles collected. Generating minimal briefing...")
        fallback = f"""---
date: {date_str}
tags: [daily-briefing, exchange, finance, AI, KRX]
---

# Daily Briefing - {date_str}

> No articles were collected today. RSS feeds may be temporarily unavailable.
> Please check feed sources and try again.

---
*Generated automatically via GitHub Actions + Gemini API*
"""
        output_path = get_output_path(date_str)
        output_path.write_text(fallback, encoding="utf-8")
        print(f"\nFallback briefing saved to: {output_path}")
        return

    # Step 2: Generate briefing via Gemini API
    print("\n[2/4] Generating briefing with Gemini API...")
    try:
        briefing_md = generate_briefing(articles, date_str)
    except Exception as e:
        print(f"\n[ERROR] Gemini API failed: {e}")
        sys.exit(1)

    # Step 3: Save to file
    print("\n[3/4] Saving briefing...")
    output_path = get_output_path(date_str)
    output_path.write_text(briefing_md, encoding="utf-8")
    print(f"\nBriefing saved to: {output_path}")
    print(f"File size: {output_path.stat().st_size:,} bytes")

    # Also create/update the latest symlink-like index
    index_path = Path(__file__).resolve().parent.parent / "briefings" / "latest.md"
    index_path.write_text(
        f"---\naliases: [latest-briefing]\n---\n\n![[{date_str}-daily-briefing]]\n",
        encoding="utf-8",
    )
    print(f"Latest index updated: {index_path}")

    # Step 4: Send to Telegram
    print("\n[4/4] Sending to Telegram...")
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        send_to_telegram(briefing_md, date_str)
    else:
        print("  Skipped (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set)")

    print("\nDone!")


if __name__ == "__main__":
    main()

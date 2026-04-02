"""Collect news articles from RSS feeds."""

import feedparser
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass


@dataclass
class Article:
    title: str
    link: str
    source: str
    published: str
    summary: str
    category: str  # "exchange_finance" or "ai_tech"


def fetch_feed(feed_config: dict, hours_back: int = 24) -> list[Article]:
    """Fetch articles from a single RSS feed within the time window."""
    articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    try:
        parsed = feedparser.parse(feed_config["url"])
        for entry in parsed.entries[:10]:  # Max 10 per feed
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            # If no date or within time window
            if published is None or published >= cutoff:
                summary = ""
                if hasattr(entry, "summary"):
                    # Strip HTML tags simply
                    import re
                    summary = re.sub(r"<[^>]+>", "", entry.summary or "")[:500]

                articles.append(
                    Article(
                        title=entry.get("title", "No Title"),
                        link=entry.get("link", ""),
                        source=feed_config["name"],
                        published=published.isoformat() if published else "Unknown",
                        summary=summary,
                        category=feed_config["category"],
                    )
                )
    except Exception as e:
        print(f"[WARN] Failed to fetch {feed_config['name']}: {e}")

    return articles


def collect_all(feeds: list[dict], hours_back: int = 24) -> dict[str, list[Article]]:
    """Collect articles from all feeds, grouped by category."""
    all_articles: dict[str, list[Article]] = {
        "exchange_finance": [],
        "ai_tech": [],
    }

    for feed in feeds:
        articles = fetch_feed(feed, hours_back)
        all_articles[feed["category"]].extend(articles)
        print(f"  Collected {len(articles)} articles from {feed['name']}")

    # Deduplicate by title similarity
    for category in all_articles:
        seen_titles = set()
        unique = []
        for article in all_articles[category]:
            title_key = article.title.lower().strip()[:60]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(article)
        all_articles[category] = unique

    return all_articles

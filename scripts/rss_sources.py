"""RSS feed sources for daily briefing."""

EXCHANGE_FINANCE_FEEDS = [
    {
        "name": "Reuters - Markets",
        "url": "https://news.google.com/rss/search?q=stock+exchange+market+infrastructure&hl=en-US&gl=US&ceid=US:en",
        "category": "exchange_finance",
    },
    {
        "name": "Financial Times - Markets",
        "url": "https://news.google.com/rss/search?q=financial+markets+clearing+settlement&hl=en-US&gl=US&ceid=US:en",
        "category": "exchange_finance",
    },
    {
        "name": "Global Exchange News",
        "url": "https://news.google.com/rss/search?q=stock+exchange+derivatives+market+regulation&hl=en-US&gl=US&ceid=US:en",
        "category": "exchange_finance",
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "category": "exchange_finance",
    },
    {
        "name": "Finextra",
        "url": "https://www.finextra.com/rss/headlines.aspx",
        "category": "exchange_finance",
    },
]

AI_TECH_FEEDS = [
    {
        "name": "Hacker News - AI",
        "url": "https://news.google.com/rss/search?q=artificial+intelligence+LLM+machine+learning&hl=en-US&gl=US&ceid=US:en",
        "category": "ai_tech",
    },
    {
        "name": "TechCrunch - AI",
        "url": "https://news.google.com/rss/search?q=site:techcrunch.com+AI+artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
        "category": "ai_tech",
    },
    {
        "name": "The Verge - AI",
        "url": "https://news.google.com/rss/search?q=site:theverge.com+AI+artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
        "category": "ai_tech",
    },
]

ALL_FEEDS = EXCHANGE_FINANCE_FEEDS + AI_TECH_FEEDS

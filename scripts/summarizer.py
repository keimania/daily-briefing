"""Summarize and translate articles using Google Gemini API (free tier)."""

import os
from google import genai
from collect_news import Article


def build_prompt(articles: dict[str, list[Article]], date_str: str) -> str:
    """Build the prompt for Gemini to summarize and translate articles."""

    exchange_section = ""
    for i, art in enumerate(articles.get("exchange_finance", [])[:15], 1):
        exchange_section += f"""
Article {i}:
- Title: {art.title}
- Source: {art.source}
- Link: {art.link}
- Summary: {art.summary}
"""

    ai_section = ""
    for i, art in enumerate(articles.get("ai_tech", [])[:10], 1):
        ai_section += f"""
Article {i}:
- Title: {art.title}
- Source: {art.source}
- Link: {art.link}
- Summary: {art.summary}
"""

    prompt = f"""You are a financial news analyst specializing in stock exchanges, derivatives markets, clearing/settlement systems, and AI technology trends.

Today's date: {date_str}

I have collected the following news articles. Please create a daily briefing in the EXACT markdown format below.

## Rules:
1. Select the TOP 5-7 most important articles for Exchange & Finance, and TOP 3-5 for AI & Tech.
2. For each selected article, write:
   - A detailed English summary (4-6 sentences). Include background context, key figures/data, and market implications.
   - A detailed Korean translation of that summary (4-6 sentences). Must convey the same depth as the English version.
3. At the end, write 3-5 key takeaways in both English and Korean.
4. Focus on news relevant to: stock exchanges, derivatives markets, clearing & settlement, market infrastructure, financial regulation, and AI/ML developments.
5. IMPORTANT: Each field (Source, Summary, 요약, Tags) MUST be on its own separate line with a blank line between each field for readability.
6. Use the exact format template below - do not deviate.

## Collected Exchange & Finance Articles:
{exchange_section}

## Collected AI & Tech Articles:
{ai_section}

## OUTPUT FORMAT (use exactly this markdown structure):

---
date: {date_str}
tags: [daily-briefing, exchange, finance, AI, KRX]
---

# Daily Briefing - {date_str}

## Exchange & Financial Markets

### 1. [Article Title](link)

**Source:** source name

**Summary (EN):**
Detailed English summary here (4-6 sentences with context, data, and implications)...

**요약 (KR):**
상세한 한국어 번역 요약 (4-6문장, 맥락, 데이터, 시사점 포함)...

**Tags:** #relevant #tags

(repeat for each selected article)

## AI & Technology

### 1. [Article Title](link)

**Source:** source name

**Summary (EN):**
Detailed English summary here (4-6 sentences with context, data, and implications)...

**요약 (KR):**
상세한 한국어 번역 요약 (4-6문장, 맥락, 데이터, 시사점 포함)...

**Tags:** #relevant #tags

(repeat for each selected article)

## Key Takeaways / 핵심 정리

| EN | KR |
|---|---|
| English point 1 | 한국어 포인트 1 |
| English point 2 | 한국어 포인트 2 |
| English point 3 | 한국어 포인트 3 |

---
*Generated automatically via GitHub Actions + Gemini API*
"""
    return prompt


def generate_briefing(articles: dict[str, list[Article]], date_str: str) -> str:
    """Call Gemini API to generate the briefing markdown."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")

    client = genai.Client(api_key=api_key)

    prompt = build_prompt(articles, date_str)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )

    return response.text

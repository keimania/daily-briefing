"""Summarize and translate articles using Google Gemini API (free tier)."""

import os
import time
from google import genai
from google.genai import types
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
   - A detailed summary synthesized from the full context (4-6 sentences covering background context, key figures/data, and market implications).
   - The summary MUST be presented in alternating English and Korean sentences for English language learning: each English sentence must be immediately followed by its natural, context-aware Korean translation on the next line.
   - Do NOT simply translate sentences in isolation. First understand the overarching story, background, and market implications, then construct precise English sentences and their natural Korean translations that accurately reflect the whole context.
   - Place a blank line between each [English sentence + Korean translation] pair for clean reading.
3. At the end, write 3-5 key takeaways in both English and Korean.
4. Focus on news relevant to: stock exchanges, derivatives markets, clearing & settlement, market infrastructure, financial regulation, and AI/ML developments.
5. IMPORTANT: Each field (Source, Summary, Tags) MUST be on its own separate line with a blank line between each field for readability.
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

**Summary:**
English sentence 1 (background context and key facts).
한국어 번역 문장 1 (문맥을 충실히 반영한 자연스러운 번역).

English sentence 2 (figures, data, or detailed developments).
한국어 번역 문장 2 (수치와 세부 사항을 반영한 자연스러운 번역).

English sentence 3 (market implications or strategic outlook).
한국어 번역 문장 3 (시장 시사점 및 전망을 담은 자연스러운 번역).

**Tags:** #relevant #tags

(repeat for each selected article)

## AI & Technology

### 1. [Article Title](link)

**Source:** source name

**Summary:**
English sentence 1 (background context and key facts).
한국어 번역 문장 1 (문맥을 충실히 반영한 자연스러운 번역).

English sentence 2 (figures, data, or detailed developments).
한국어 번역 문장 2 (수치와 세부 사항을 반영한 자연스러운 번역).

English sentence 3 (market implications or strategic outlook).
한국어 번역 문장 3 (시장 시사점 및 전망을 담은 자연스러운 번역).

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
    """Call Gemini API to generate the briefing markdown with retry and fallback."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(articles, date_str)

    models_to_try = [
        (
            "gemini-3.8-flash",
            types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="MEDIUM")
            ),
        ),
        (
            "gemini-2.5-flash",
            None,
        ),
    ]

    last_error = None
    for model_name, cfg in models_to_try:
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Calling Gemini API with {model_name} (attempt {attempt}/{max_retries})...")
                kwargs = {"model": model_name, "contents": prompt}
                if cfg:
                    kwargs["config"] = cfg
                response = client.models.generate_content(**kwargs)
                if response.text:
                    return response.text
            except Exception as e:
                last_error = e
                err_msg = str(e)
                print(f"[WARN] {model_name} attempt {attempt} failed: {err_msg}")
                # If temporary overload (503) or rate limit (429), wait and retry
                if attempt < max_retries and any(code in err_msg for code in ["503", "429", "UNAVAILABLE"]):
                    wait_sec = attempt * 7
                    print(f"Waiting {wait_sec}s before retrying {model_name}...")
                    time.sleep(wait_sec)
                else:
                    break

    raise RuntimeError(f"All Gemini API attempts failed. Last error: {last_error}")

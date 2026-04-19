"""
뉴스 요약 스크립트
Groq API (무료)를 사용해 수집된 뉴스를 카카오톡 전송용으로 요약합니다.
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from fetch_news import fetch_all_news

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT_TEMPLATE = """당신은 뉴스 큐레이터입니다. 아래 {category} 뉴스를 요약해주세요.

규칙:
- 기사별로 핵심 내용 한 줄 요약
- 전체 300자 이내
- 불필요한 인사말 없이 바로 요약만 작성

뉴스:
{news_data}
"""


def summarize_category(category: str, articles: list[dict]) -> str:
    """카테고리 하나를 Groq API로 요약합니다."""
    lines = []
    for a in articles:
        lines.append(f"- {a['title']}")
        if a.get("description"):
            lines.append(f"  {a['description'][:100]}")

    prompt = PROMPT_TEMPLATE.format(category=category, news_data="\n".join(lines))

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0.7,
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except (requests.RequestException, KeyError) as e:
        print(f"[오류] {category} 요약 실패: {e}")
        return ""


def summarize_all(all_news: dict[str, list[dict]]) -> dict[str, str]:
    """전체 카테고리를 각각 요약합니다."""
    result = {}
    for category, articles in all_news.items():
        if not articles:
            continue
        print(f"  → {category} 요약 중...")
        summary = summarize_category(category, articles)
        if summary:
            result[category] = summary
    return result


def build_category_message(category: str, summary: str) -> str:
    now = datetime.now().strftime("%m/%d %H:%M")
    return f"{category}\n{now}\n{'─' * 18}\n{summary}"


if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("[오류] GROQ_API_KEY 환경변수가 없습니다.")
        exit(1)

    print("[1/2] 뉴스 수집 중...")
    news = fetch_all_news(max_per_category=3)

    print("[2/2] Groq AI로 카테고리별 요약 중...")
    summaries = summarize_all(news)

    for category, summary in summaries.items():
        print("\n" + "=" * 40)
        print(build_category_message(category, summary))
        print("=" * 40)

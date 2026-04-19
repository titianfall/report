"""
뉴스 요약 스크립트
Claude API를 사용해 수집된 뉴스를 카카오톡 전송용으로 요약합니다.
"""

import os
import anthropic
from datetime import datetime
from dotenv import load_dotenv
from fetch_news import fetch_all_news

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """당신은 바쁜 직장인을 위한 뉴스 큐레이터입니다.
수집된 뉴스 기사들을 간결하고 읽기 쉽게 요약해주세요.
카카오톡 메시지 형식에 맞게 이모지를 적절히 활용하고,
각 기사는 2~3줄 이내로 핵심만 전달하세요."""

USER_PROMPT_TEMPLATE = """다음 뉴스 기사들을 카카오톡 메시지용으로 요약해주세요.

형식:
- 날짜/시간 헤더
- 카테고리별 구분
- 각 기사: 제목 + 한줄 요약
- 마지막에 오늘의 한마디 (동기부여 문구)

뉴스 데이터:
{news_data}
"""


def format_news_for_prompt(all_news: dict[str, list[dict]]) -> str:
    """Claude 프롬프트용으로 뉴스 데이터를 포맷합니다."""
    lines = []
    for category, articles in all_news.items():
        lines.append(f"\n[{category}]")
        for a in articles:
            lines.append(f"- 제목: {a['title']}")
            if a.get("description"):
                lines.append(f"  내용: {a['description'][:150]}")
    return "\n".join(lines)


def summarize_news(all_news: dict[str, list[dict]]) -> str:
    """Claude API로 뉴스를 요약합니다."""
    news_text = format_news_for_prompt(all_news)
    prompt = USER_PROMPT_TEMPLATE.format(news_data=news_text)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    except anthropic.APIError as e:
        print(f"[오류] Claude API 호출 실패: {e}")
        return ""


def build_kakao_message(summary: str) -> str:
    """카카오톡 전송용 최종 메시지를 구성합니다."""
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    header = f"📰 오늘의 뉴스 브리핑\n{now}\n{'─' * 20}\n"
    return header + summary


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[오류] ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        exit(1)

    print("[1/2] 뉴스 수집 중...")
    news = fetch_all_news(max_per_category=5)

    print("[2/2] Claude API로 요약 중...")
    summary = summarize_news(news)

    if summary:
        message = build_kakao_message(summary)
        print("\n" + "=" * 40)
        print(message)
        print("=" * 40)
    else:
        print("[오류] 요약 생성에 실패했습니다.")

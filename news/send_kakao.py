"""
카카오톡 전송 스크립트
뉴스 리스트를 카카오톡 나에게 보내기로 전송합니다. (제목 클릭 시 기사 이동)
"""

import os
import json
import requests
from dotenv import load_dotenv
import time
from fetch_news import fetch_all_news
from summarize import summarize_all, build_category_message

load_dotenv()

KAKAO_ACCESS_TOKEN = os.getenv("KAKAO_ACCESS_TOKEN")
KAKAO_API_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


def build_text_message(all_news: dict) -> str:
    """클릭 가능한 URL이 포함된 텍스트 메시지를 생성합니다."""
    from datetime import datetime
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    lines = [f"📰 오늘의 뉴스 브리핑\n{now}\n{'─' * 20}"]

    emoji_map = {}  # 카테고리명에 이모지 포함됨

    for category, articles in all_news.items():
        if not articles:
            continue
        lines.append(f"\n{category}")
        for a in articles:
            title = a["title"] or ""
            url = a.get("url", "")
            lines.append(f"• {title}")
            if url:
                lines.append(f"  {url}")

    return "\n".join(lines)


def send_kakao_text(text: str) -> bool:
    """카카오톡 나에게 보내기 - 텍스트 전송."""
    headers = {
        "Authorization": f"Bearer {KAKAO_ACCESS_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    template = {
        "object_type": "text",
        "text": text[:950].rsplit("\n", 1)[0] if len(text) > 950 else text,
        "link": {"web_url": "", "mobile_web_url": ""},
    }

    try:
        response = requests.post(
            KAKAO_API_URL,
            headers=headers,
            data={"template_object": json.dumps(template, ensure_ascii=False)},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("result_code") == 0:
            print("[성공] 카카오톡 전송 완료!")
            return True
        else:
            print(f"[오류] 카카오 응답: {result}")
            return False

    except requests.RequestException as e:
        print(f"[오류] 카카오톡 전송 실패: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"  상세: {e.response.text}")
        return False


def run_pipeline() -> None:
    """뉴스 수집 → 포맷 → 카카오톡 전송 파이프라인."""
    if not KAKAO_ACCESS_TOKEN:
        print("[오류] KAKAO_ACCESS_TOKEN 환경변수가 없습니다.")
        return

    print("[1/3] 뉴스 수집 중...")
    news = fetch_all_news(max_per_category=3)

    print("[2/3] Groq AI 카테고리별 요약 중...")
    summaries = summarize_all(news)
    if not summaries:
        print("[오류] 요약 실패로 전송 중단")
        return

    print("[3/3] 카카오톡 전송 중...")
    for i, (category, summary) in enumerate(summaries.items()):
        message = build_category_message(category, summary)
        send_kakao_text(message)
        if i < len(summaries) - 1:
            time.sleep(1)  # 연속 전송 간격


if __name__ == "__main__":
    run_pipeline()

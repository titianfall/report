"""
카카오톡 전송 스크립트
카카오 API를 사용해 나에게 보내기로 뉴스 요약을 전송합니다.
"""

import os
import requests
from dotenv import load_dotenv
from fetch_news import fetch_all_news
from summarize import summarize_news, build_kakao_message

load_dotenv()

KAKAO_ACCESS_TOKEN = os.getenv("KAKAO_ACCESS_TOKEN")
KAKAO_API_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


def send_kakao_message(text: str) -> bool:
    """카카오톡 나에게 보내기로 메시지를 전송합니다."""
    headers = {
        "Authorization": f"Bearer {KAKAO_ACCESS_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # 카카오 텍스트 템플릿 형식
    template = {
        "object_type": "text",
        "text": text[:1000],  # 카카오 최대 1000자 제한
        "link": {
            "web_url": "https://github.com/titianfall/report",
            "mobile_web_url": "https://github.com/titianfall/report",
        },
    }

    try:
        response = requests.post(
            KAKAO_API_URL,
            headers=headers,
            data={"template_object": str(template).replace("'", '"')},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("result_code") == 0:
            print("[성공] 카카오톡 메시지 전송 완료!")
            return True
        else:
            print(f"[오류] 카카오 응답 오류: {result}")
            return False

    except requests.RequestException as e:
        print(f"[오류] 카카오톡 전송 실패: {e}")
        return False


def refresh_kakao_token(refresh_token: str) -> str | None:
    """카카오 액세스 토큰을 갱신합니다."""
    rest_api_key = os.getenv("KAKAO_REST_API_KEY")
    if not rest_api_key:
        print("[오류] KAKAO_REST_API_KEY 환경변수가 없습니다.")
        return None

    try:
        response = requests.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": rest_api_key,
                "refresh_token": refresh_token,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        new_token = data.get("access_token")
        if new_token:
            print("[갱신] 카카오 액세스 토큰이 갱신되었습니다.")
        return new_token

    except requests.RequestException as e:
        print(f"[오류] 토큰 갱신 실패: {e}")
        return None


def run_pipeline() -> None:
    """뉴스 수집 → 요약 → 카카오톡 전송 전체 파이프라인을 실행합니다."""
    if not KAKAO_ACCESS_TOKEN:
        print("[오류] KAKAO_ACCESS_TOKEN 환경변수가 설정되지 않았습니다.")
        print("  카카오 개발자 콘솔에서 토큰을 발급 후 .env에 추가하세요.")
        return

    print("[1/3] 뉴스 수집 중...")
    news = fetch_all_news(max_per_category=5)

    print("[2/3] 뉴스 요약 중...")
    summary = summarize_news(news)
    if not summary:
        print("[오류] 요약 실패로 전송을 중단합니다.")
        return

    message = build_kakao_message(summary)
    print("\n전송할 메시지 미리보기:")
    print("=" * 40)
    print(message[:500] + ("..." if len(message) > 500 else ""))
    print("=" * 40)

    print("[3/3] 카카오톡 전송 중...")
    send_kakao_message(message)


if __name__ == "__main__":
    run_pipeline()

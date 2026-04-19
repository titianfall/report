"""
뉴스 수집 스크립트
NewsAPI를 사용해 IT/테크, 국내, 비즈니스/스타트업 뉴스를 수집합니다.
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"

CATEGORIES = {
    "💻 IT/과학": {
        "q": "AI OR 인공지능 OR 반도체 OR 개발자 OR 클라우드 OR 빅데이터 OR 사이버보안",
        "language": "ko",
    },
    "🚀 스타트업/테크": {
        "q": "스타트업 OR 유니콘 OR 투자 OR 시리즈A OR 시리즈B OR 앱 OR 플랫폼",
        "language": "ko",
    },
    "💼 취업/채용": {
        "q": "취업 OR 채용 OR 구직 OR 이직 OR 신입 OR 공채 OR 커리어",
        "language": "ko",
    },
    "💰 경제": {
        "q": "주식 OR 코스피 OR 환율 OR 금리 OR 부동산 OR 물가 OR 경기",
        "language": "ko",
    },
    "🌏 사회": {
        "q": "정책 OR 정부 OR 사회 OR 교육 OR 복지",
        "language": "ko",
    },
}


def fetch_articles(category: str, params: dict, max_results: int = 5) -> list[dict]:
    """특정 카테고리의 뉴스 기사를 수집합니다."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    query_params = {
        "apiKey": NEWS_API_KEY,
        "from": yesterday,
        "sortBy": "publishedAt",
        "pageSize": max_results,
        **params,
    }

    try:
        response = requests.get(BASE_URL, params=query_params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get("articles", []):
            articles.append({
                "category": category,
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", ""),
                "published_at": article.get("publishedAt", ""),
            })
        return articles

    except requests.RequestException as e:
        print(f"[오류] {category} 뉴스 수집 실패: {e}")
        return []


def fetch_all_news(max_per_category: int = 5) -> dict[str, list[dict]]:
    """모든 카테고리의 뉴스를 수집합니다."""
    all_news = {}

    for category, params in CATEGORIES.items():
        print(f"[수집 중] {category}...")
        articles = fetch_articles(category, params, max_per_category)
        all_news[category] = articles
        print(f"  → {len(articles)}건 수집 완료")

    return all_news


def format_for_display(all_news: dict[str, list[dict]]) -> str:
    """수집된 뉴스를 보기 좋게 포맷합니다."""
    lines = [f"📰 뉴스 수집 결과 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"]

    for category, articles in all_news.items():
        lines.append(f"\n【{category}】")
        if not articles:
            lines.append("  - 수집된 기사 없음")
            continue
        for i, a in enumerate(articles, 1):
            lines.append(f"  {i}. {a['title']}")
            lines.append(f"     출처: {a['source']} | {a['published_at'][:10]}")

    return "\n".join(lines)


if __name__ == "__main__":
    if not NEWS_API_KEY:
        print("[오류] NEWS_API_KEY 환경변수가 설정되지 않았습니다.")
        print("  .env 파일에 NEWS_API_KEY=your_key_here 를 추가하세요.")
        exit(1)

    news = fetch_all_news(max_per_category=5)
    print(format_for_display(news))

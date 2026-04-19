"""
카카오 액세스 토큰 발급 스크립트
브라우저로 로그인 후 자동으로 토큰을 발급받습니다.
"""

import os
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from dotenv import load_dotenv

load_dotenv()

REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
REDIRECT_URI = "http://localhost:5000/callback"


class CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>✅ 인증 완료! 터미널로 돌아가세요.</h2>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 로그 출력 억제


def get_access_token(auth_code: str) -> dict:
    """인증 코드로 액세스 토큰을 발급받습니다."""
    response = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": REST_API_KEY,
            "redirect_uri": REDIRECT_URI,
            "code": auth_code,
        },
        timeout=10,
    )
    return response.json()


if __name__ == "__main__":
    if not REST_API_KEY:
        print("[오류] KAKAO_REST_API_KEY가 .env에 없습니다.")
        exit(1)

    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={REST_API_KEY}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&response_type=code"
    )

    print("[1/3] 브라우저에서 카카오 로그인을 진행해주세요...")
    webbrowser.open(auth_url)

    print("[2/3] 로그인 대기 중... (로그인 완료 후 자동 진행)")
    server = HTTPServer(("localhost", 5000), CallbackHandler)
    server.handle_request()  # 콜백 1회만 처리

    if not CallbackHandler.auth_code:
        print("[오류] 인증 코드를 받지 못했습니다.")
        exit(1)

    print("[3/3] 액세스 토큰 발급 중...")
    token_data = get_access_token(CallbackHandler.auth_code)

    if "access_token" in token_data:
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token", "")

        print("\n✅ 토큰 발급 성공!")
        print(f"ACCESS_TOKEN:  {access_token}")
        print(f"REFRESH_TOKEN: {refresh_token}")
        print("\n아래 내용을 .env 파일에 추가하세요:")
        print(f"KAKAO_ACCESS_TOKEN={access_token}")
        print(f"KAKAO_REFRESH_TOKEN={refresh_token}")
    else:
        print(f"[오류] 토큰 발급 실패: {token_data}")

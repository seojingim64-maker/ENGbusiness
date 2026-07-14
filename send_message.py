"""
매일 카카오톡 '나에게 보내기'로 비즈니스 영어 표현을 발송하는 스크립트.
서버 불필요 - GitHub Actions 스케줄러(cron)로 하루 한 번 실행됩니다.

동작 방식:
- expressions.json 에 담긴 22개 표현 중, 오늘 순번에 해당하는 "1개"만 골라서 발송
- 그 표현의 핵심 표현(core_expression) + 뜻 + 예문 5개 + 타임스탬프 유튜브 링크를
  카카오톡 Feed 템플릿(썸네일 이미지 포함) 메시지 1건으로 전송
- 22개를 다 보내면 다시 처음(1번)부터 순환

필요한 환경변수 (GitHub Secrets에 등록):
  KAKAO_REST_API_KEY  - 카카오 개발자 앱의 REST API 키
  KAKAO_REFRESH_TOKEN - 최초 1회 발급받은 리프레시 토큰
"""
import os
import json
import requests

REST_API_KEY = os.environ["KAKAO_REST_API_KEY"]
REFRESH_TOKEN = os.environ["KAKAO_REFRESH_TOKEN"]

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
STATE_FILE = "state.json"
DATA_FILE = "expressions.json"

# 카카오 Feed 템플릿 description 필드는 넉넉히 잡아도 400자 내외가 안전.
# 넘칠 경우를 대비해 안전하게 잘라내는 버퍼.
MAX_DESCRIPTION_CHARS = 450


def get_access_token() -> str:
    """리프레시 토큰으로 액세스 토큰을 새로 발급받는다."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": REST_API_KEY,
            "refresh_token": REFRESH_TOKEN,
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def load_state() -> dict:
    """마지막으로 보낸 표현의 순번을 기억해둔다 (없으면 처음부터)."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"sent_index": -1}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def format_timestamp(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def build_description(item: dict) -> str:
    """뜻 + 예문 5개를 하나의 설명 텍스트로 구성 (길이 제한 대비 트림 포함)."""
    lines = [f"👉 {item['meaning_kr']}", "", "예문 5개:"]
    for i, ex in enumerate(item["examples"], start=1):
        lines.append(f"{i}. {ex}")
    text = "\n".join(lines)

    if len(text) > MAX_DESCRIPTION_CHARS:
        text = text[: MAX_DESCRIPTION_CHARS - 1] + "…"
    return text


def build_message(item: dict, day_no: int, total: int) -> dict:
    link = f"https://youtu.be/{item['video_id']}?t={item['timestamp_seconds']}"
    thumbnail = f"https://img.youtube.com/vi/{item['video_id']}/hqdefault.jpg"
    ts = format_timestamp(item["timestamp_seconds"])

    title = f"[Day {day_no}/{total}] {item['core_expression']}"
    description = build_description(item)

    template_object = {
        "object_type": "feed",
        "content": {
            "title": title,
            "description": description,
            "image_url": thumbnail,
            "image_width": 640,
            "image_height": 360,
            "link": {"web_url": link, "mobile_web_url": link},
        },
        "buttons": [
            {
                "title": f"영상에서 보기 ({ts}~)",
                "link": {"web_url": link, "mobile_web_url": link},
            }
        ],
    }
    return template_object


def send_to_me(access_token: str, template_object: dict) -> dict:
    resp = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template_object, ensure_ascii=False)},
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        expressions = json.load(f)

    state = load_state()
    next_index = (state["sent_index"] + 1) % len(expressions)
    item = expressions[next_index]

    access_token = get_access_token()
    template_object = build_message(item, next_index + 1, len(expressions))
    result = send_to_me(access_token, template_object)
    print(f"발송 완료 (Day {next_index + 1}/{len(expressions)}):", result)

    state["sent_index"] = next_index
    save_state(state)


if __name__ == "__main__":
    main()

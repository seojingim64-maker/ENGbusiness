# 매일 아침 비즈니스 영어 - 카카오톡 "나에게 보내기" (개인 테스트용)

서버 없이, 매일 08:30(KST)에 GitHub Actions가 카카오톡으로
**오늘의 표현 1개**(핵심 표현 + 뜻 + 예문 5개 + 영상 링크)를 본인 계정으로 보내주는 구성입니다.

소스 영상: 삶은영어 채널 "더 오피스" 시리즈 1편 (표현 22개 → 하루 1개씩, 22일 순환)

---

## 1. 카카오 개발자 앱 만들기 (5분)

1. https://developers.kakao.com 접속 → 로그인 → **내 애플리케이션 → 애플리케이션 추가**
2. 앱 이름은 아무거나 (예: "모닝잉글리시") 입력 후 저장
3. **앱 설정 → 요약 정보**에서 **REST API 키** 복사해두기 (나중에 Secret으로 사용)
4. **제품 설정 → 카카오 로그인** → 활성화 ON
5. **카카오 로그인 → Redirect URI 등록**: `https://localhost.com` 처럼 아무 값이나 하나 등록
   (실제로 접속되는 서버가 아니어도 됩니다. 인가 코드만 받으면 되는 용도)
6. **카카오 로그인 → 동의항목**에서 **"카카오톡 메시지 전송"** 항목을 찾아 **필수 동의**로 설정
   - 개인 계정(본인)만 쓸 거라 별도 검수 없이 바로 사용 가능합니다

## 2. 인가 코드 → 토큰 발급받기 (1회만 하면 됨)

**① 아래 URL의 {REST_API_KEY}와 {REDIRECT_URI}를 본인 값으로 바꿔서 브라우저 주소창에 입력:**

```
https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code&scope=talk_message
```

동의 화면에서 동의 → 리다이렉트된 주소(`https://localhost.com/?code=...`)에서
`code=` 뒤에 붙은 값을 복사합니다.

**② 터미널에서 아래 curl 명령 실행** (본인 값으로 치환):

```bash
curl -X POST "https://kauth.kakao.com/oauth/token" \
  -d "grant_type=authorization_code" \
  -d "client_id={REST_API_KEY}" \
  -d "redirect_uri={REDIRECT_URI}" \
  -d "code={방금 받은 인가코드}"
```

응답 JSON에서 `refresh_token` 값을 복사해두세요.

## 3. GitHub 레포에 올리고 Secrets 등록

1. 이 폴더를 새 GitHub 레포에 push (Private 추천)
2. 레포 → **Settings → Secrets and variables → Actions → New repository secret**
3. 등록: `KAKAO_REST_API_KEY`, `KAKAO_REFRESH_TOKEN`

## 4. 테스트 실행

**Actions 탭 → Daily Kakao English Message → Run workflow** 로 즉시 수동 실행 가능합니다.
성공하면 본인 카카오톡 "나와의 채팅"에 메시지가 도착합니다. 이후 평일 매일 08:30(KST) 자동 실행됩니다.

---

## 메시지 구성

하루에 **표현 1개만** 발송되며, 메시지 안에는:

- 핵심 표현 (제목)
- 한국어 뜻
- 예문 5개
- 영상 썸네일 이미지
- 해당 표현이 나오는 정확한 시점으로 이동하는 유튜브 링크 버튼

이 모두 담깁니다. `state.json`이 "몇 번째까지 보냈는지" 기억하고 있어서,
22개를 다 보내면 자동으로 1번으로 돌아가 다시 순환합니다.

## 알아두면 좋은 제약사항

- **카카오톡 Feed 메시지의 설명(description) 글자 수는 넉넉히 400자 내외가 안전선**이에요.
  예문 5개 + 뜻을 다 넣으면 표현에 따라 이 근처까지 찰 수 있어서, 코드에 자동으로
  초과분을 잘라내는 안전장치(`MAX_DESCRIPTION_CHARS`)를 넣어뒀습니다. 실제 발송 후 메시지가
  잘려 보이면 `send_message.py`의 `MAX_DESCRIPTION_CHARS` 값을 조절하거나 예문을 더 축약하세요.
- **"나에게 보내기" API는 본인 카카오 계정 1명에게만** 보낼 수 있어요. 여러 사람에게 보내려면
  카카오 비즈메시지(친구톡/알림톡) 사업자 심사가 별도로 필요합니다.
- `refresh_token`은 보통 두 달 정도 유효기간이 있어서, 만료되면 2번 과정을 다시 한 번 해줘야 합니다.
- 원본 영상이 저작권 클레임 등으로 내려갈 경우, 링크가 깨질 수 있습니다.
  본격 운영 단계에서는 발송 전 링크 생존 여부를 확인하는 로직 추가를 권장합니다.

## 콘텐츠 늘리는 법

`expressions.json`에 같은 구조로 항목을 추가하면 됩니다:

```json
{
  "video_id": "유튜브 영상ID",
  "video_title": "영상 제목",
  "timestamp_seconds": 등장시점(초),
  "original_line": "영상 속 원문 대사",
  "core_expression": "재사용 가능한 핵심 표현 패턴",
  "meaning_kr": "한국어 뜻/사용 상황",
  "examples": ["예문1", "예문2", "예문3", "예문4", "예문5"]
}
```

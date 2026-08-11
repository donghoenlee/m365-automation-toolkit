"""Claude API를 이용한 헬프데스크 문의 자동 분류 + 초안 답변 생성.

IT 헬프데스크로 들어오는 문의를 담당자가 매번 읽고 분류/라우팅하는 대신,
카테고리·우선순위·관리자 조치 필요 여부를 자동 판별하고 1차 답변 초안까지
생성해 담당자는 검토/발송만 하면 되도록 한다.
"""

import json

from anthropic import Anthropic

import config

CATEGORIES = [
    "계정/비밀번호",
    "라이선스 요청",
    "메일/공유함 접근",
    "MFA/보안",
    "네트워크/VPN",
    "소프트웨어 설치",
    "기타",
]

SYSTEM_PROMPT = f"""너는 IT 인프라 운영팀의 헬프데스크 티켓 분류 어시스턴트다.
사용자 문의를 읽고 아래 JSON 스키마로만 답하라. 다른 텍스트는 절대 포함하지 마라.

{{
  "category": "{' | '.join(CATEGORIES)} 중 하나",
  "priority": "높음 | 보통 | 낮음",
  "needs_admin_action": true 또는 false,
  "summary": "문의 내용 한 줄 요약",
  "draft_reply": "담당자가 그대로 보내도 될 정도의 정중한 한국어 초안 답변 (2~4문장)"
}}
"""


def classify_ticket(subject: str, body: str) -> dict:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env를 확인하세요.")

    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"제목: {subject}\n내용: {body}"}],
    )

    text = message.content[0].text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        raise ValueError(f"모델 응답을 JSON으로 파싱하지 못했습니다: {text}")

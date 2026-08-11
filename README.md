# M365 관리 자동화 툴킷

Microsoft 365 환경에서 IT 관리자가 반복적으로 처리하는 3가지 업무를 자동화하는 Streamlit 대시보드입니다.

- **사용자 라이프사이클 자동화**: 입사자 온보딩(계정 생성 → 라이선스 할당 → 그룹 추가)과 퇴사자 오프보딩(계정 비활성화 → 로그인 세션 강제 종료)을 여러 관리 포털을 오가지 않고 한 번에 처리
- **라이선스·보안 감사 리포트**: 라이선스 사용률, MFA 미등록 계정, 장기 미로그인 계정을 자동 집계
- **헬프데스크 어시스턴트**: Claude API로 문의를 자동 분류(카테고리/우선순위)하고 답변 초안을 생성해 담당자는 검토·발송만 하면 되도록 지원

## 왜 만들었나

Microsoft Graph API로 대부분 자동화할 수 있는데도, 실제로는 관리자가 Entra 관리센터·Exchange 관리센터·Teams 관리센터를 오가며 수작업으로 처리하는 경우가 많습니다. 이 툴킷은 그 반복 작업을 스크립트 + 대시보드로 대체하는 것을 목표로 합니다.

## 아키텍처

```
app.py, pages/            Streamlit UI
modules/                  업무 로직 (lifecycle, audit, helpdesk)
graph/client.py           GraphClient 추상 인터페이스
graph/mock_client.py      로컬 JSON 기반 목업 구현체
graph/real_client.py      MSAL + Microsoft Graph API 실제 구현체
```

`modules/*`는 `GraphClient` 인터페이스에만 의존하므로, `.env`의 `USE_MOCK_GRAPH` 값만 바꾸면
동일한 코드가 목업 데이터 또는 실제 테넌트 어느 쪽으로도 동작합니다.

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env          # macOS/Linux: cp .env.example .env
# .env에 ANTHROPIC_API_KEY 입력 (헬프데스크 기능에 필요)

streamlit run app.py
```

기본값(`USE_MOCK_GRAPH=true`)으로 실행하면 실제 M365 테넌트 없이 목업 데이터(사용자 8명, 라이선스 3종)로
전체 기능을 바로 체험할 수 있습니다.

## 테스트

```bash
pytest
```

목업 클라이언트를 기준으로 온보딩/오프보딩/감사 리포트 로직을 검증합니다.

## 실제 M365 테넌트 연동하기

1. [Microsoft 365 Developer Program](https://developer.microsoft.com/microsoft-365/dev-program) 또는 30일 체험판으로 테넌트 준비
2. [Entra 관리센터](https://entra.microsoft.com) → **앱 등록(App registrations)** → 새 등록
3. **API 권한**에서 Application 권한 추가 후 관리자 동의:
   - `User.ReadWrite.All`
   - `Group.ReadWrite.All`
   - `Directory.Read.All`
   - `Reports.Read.All` (MFA/로그인 활동 조회용)
4. **인증서 및 암호(Certificates & secrets)** → 새 클라이언트 암호 생성
5. `.env`에 `USE_MOCK_GRAPH=false`와 함께 `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET` 입력

코드 변경 없이 `graph/real_client.py`가 자동으로 사용됩니다.

## 기술 스택

Python · Streamlit · Microsoft Graph API (MSAL) · Claude API (Anthropic) · pandas · pytest

## 향후 개선 아이디어

- Teams 웹훅 연동으로 감사 리포트 정기 알림 발송
- Intune 기기 컴플라이언스 현황 모듈 추가
- 온보딩/오프보딩 승인 워크플로 (담당자 승인 후 실행)

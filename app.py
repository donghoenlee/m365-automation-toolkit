import streamlit as st

import config
from graph.client import get_graph_client
from modules import audit

st.set_page_config(page_title="M365 관리 자동화 툴킷", page_icon="🧰", layout="wide")

st.title("🧰 M365 관리 자동화 툴킷")
st.caption("Microsoft Graph API + Claude API 기반 IT 인프라 운영 자동화 대시보드")

mode = "🧪 목업 모드 (mock)" if config.USE_MOCK_GRAPH else "🔗 실제 Graph API 연동"
st.info(f"현재 데이터 소스: **{mode}**  ·  `.env`의 `USE_MOCK_GRAPH` 값으로 전환합니다.")

client = get_graph_client()
users = client.list_users()
licenses = client.list_licenses()

active_users = [u for u in users if u.get("accountEnabled")]
no_mfa = [u for u in users if not u.get("mfaRegistered")]
inactive_df = audit.inactive_accounts_report(client, days=config.INACTIVE_DAYS_THRESHOLD)

col1, col2, col3, col4 = st.columns(4)
col1.metric("전체 사용자", len(users))
col2.metric("활성 계정", len(active_users))
col3.metric("MFA 미등록", len(no_mfa), delta=None, delta_color="inverse")
col4.metric(f"{config.INACTIVE_DAYS_THRESHOLD}일 이상 미로그인", len(inactive_df))

st.divider()
st.subheader("라이선스 현황")
st.dataframe(audit.license_utilization_report(client), width="stretch", hide_index=True)

st.divider()
st.markdown(
    """
### 이 툴킷이 하는 일
- **사용자 라이프사이클**: 입사자 온보딩(계정 생성·라이선스 할당·그룹 추가) / 퇴사자 오프보딩(비활성화·세션 종료)을 한 번에 처리
- **라이선스·보안 감사**: 미사용 라이선스, MFA 미등록 계정, 장기 미로그인 계정을 자동 리포트
- **헬프데스크 어시스턴트**: Claude API로 문의 자동 분류 + 초안 답변 생성

왼쪽 사이드바에서 각 기능 페이지로 이동하세요.
"""
)

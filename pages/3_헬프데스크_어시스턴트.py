import json
import os

import streamlit as st

from modules import helpdesk

st.set_page_config(page_title="헬프데스크 어시스턴트", page_icon="🤖", layout="wide")
st.title("🤖 IT 헬프데스크 어시스턴트")
st.caption("Claude API로 문의를 자동 분류하고 답변 초안을 생성합니다. 담당자는 검토 후 발송만 하면 됩니다.")

TICKETS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tickets_sample.json")
with open(TICKETS_PATH, encoding="utf-8") as f:
    sample_tickets = json.load(f)

source = st.radio("문의 입력 방식", ["샘플 티켓에서 선택", "직접 입력"], horizontal=True)

if source == "샘플 티켓에서 선택":
    labels = {f"[{t['id']}] {t['subject']} — {t['requester']}": t for t in sample_tickets}
    chosen = st.selectbox("티켓 선택", list(labels.keys()))
    ticket = labels[chosen]
    subject, body = ticket["subject"], ticket["body"]
    st.text_area("문의 내용", body, height=100, disabled=True)
else:
    subject = st.text_input("제목", placeholder="비밀번호 초기화 요청")
    body = st.text_area("내용", placeholder="계정에 로그인이 안 됩니다...", height=100)

if st.button("분류 및 답변 초안 생성", type="primary"):
    if not subject or not body:
        st.error("제목과 내용을 입력하세요.")
    else:
        with st.spinner("Claude가 문의를 분석하는 중..."):
            try:
                result = helpdesk.classify_ticket(subject, body)
            except Exception as e:
                st.error(f"분류 실패: {e}")
                result = None

        if result:
            priority_color = {"높음": "🔴", "보통": "🟡", "낮음": "🟢"}.get(result["priority"], "⚪")
            c1, c2, c3 = st.columns(3)
            c1.metric("카테고리", result["category"])
            c2.metric("우선순위", f"{priority_color} {result['priority']}")
            c3.metric("관리자 조치 필요", "예" if result["needs_admin_action"] else "아니오")

            st.markdown(f"**요약**: {result['summary']}")
            st.text_area("답변 초안 (복사해서 사용)", result["draft_reply"], height=140)

st.divider()
st.caption("전체 카테고리: " + " · ".join(helpdesk.CATEGORIES))

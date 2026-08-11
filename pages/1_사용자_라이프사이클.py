import streamlit as st

from graph.client import get_graph_client
from modules import lifecycle

st.set_page_config(page_title="사용자 라이프사이클", page_icon="👤", layout="wide")
st.title("👤 사용자 라이프사이클 자동화")

client = get_graph_client()

tab_onboard, tab_offboard = st.tabs(["신규 입사자 온보딩", "퇴사자 오프보딩"])

with tab_onboard:
    st.caption("계정 생성 → 라이선스 할당 → 그룹 추가를 한 번에 처리합니다.")
    with st.form("onboard_form"):
        c1, c2 = st.columns(2)
        display_name = c1.text_input("이름", placeholder="홍길동")
        mail_nickname = c2.text_input("메일 별칭 (영문)", placeholder="gildong.hong")
        department = c1.text_input("부서", placeholder="IT")
        job_title = c2.text_input("직책", placeholder="사원")

        licenses = client.list_licenses()
        license_options = {lic["displayName"]: lic["skuPartNumber"] for lic in licenses}
        license_label = st.selectbox("할당할 라이선스", ["없음"] + list(license_options.keys()))

        groups = st.multiselect("추가할 그룹", client.list_groups(), default=["All Staff"])

        submitted = st.form_submit_button("온보딩 실행", type="primary")

    if submitted:
        if not display_name or not mail_nickname:
            st.error("이름과 메일 별칭은 필수입니다.")
        else:
            profile = {
                "displayName": display_name,
                "mailNickname": mail_nickname,
                "department": department,
                "jobTitle": job_title,
                "license_sku": license_options.get(license_label) if license_label != "없음" else None,
                "groups": groups,
            }
            log = lifecycle.onboard_user(client, profile)
            st.success(f"{display_name} 온보딩 처리 완료")
            for entry in log:
                icon = {"성공": "✅", "실패": "❌"}.get(entry["status"], "ℹ️")
                st.write(f"{icon} **{entry['step']}** — {entry['detail']}")

with tab_offboard:
    st.caption("계정 비활성화 및 로그인 세션 강제 종료를 처리합니다.")
    users = client.list_users()
    active_users = {f"{u['displayName']} ({u['userPrincipalName']})": u["id"] for u in users if u["accountEnabled"]}

    if not active_users:
        st.info("비활성화할 활성 계정이 없습니다.")
    else:
        target_label = st.selectbox("퇴사 처리할 사용자", list(active_users.keys()))
        if st.button("오프보딩 실행", type="primary"):
            log = lifecycle.offboard_user(client, active_users[target_label])
            st.success(f"{target_label} 오프보딩 처리 완료")
            for entry in log:
                icon = {"성공": "✅", "실패": "❌", "안내": "📌"}.get(entry["status"], "ℹ️")
                st.write(f"{icon} **{entry['step']}** — {entry['detail']}")

st.divider()
st.subheader("전체 사용자 목록")
st.dataframe(
    [
        {
            "이름": u["displayName"],
            "UPN": u["userPrincipalName"],
            "부서": u.get("department", ""),
            "상태": "활성" if u["accountEnabled"] else "비활성",
            "라이선스": ", ".join(u.get("assignedLicenses", [])) or "-",
            "그룹": ", ".join(u.get("groups", [])) or "-",
        }
        for u in client.list_users()
    ],
    width="stretch",
    hide_index=True,
)

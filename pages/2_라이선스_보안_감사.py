import streamlit as st

import config
from graph.client import get_graph_client
from modules import audit

st.set_page_config(page_title="라이선스·보안 감사", page_icon="🛡️", layout="wide")
st.title("🛡️ 라이선스·보안 감사 리포트")
st.caption("매월 수작업으로 확인하던 라이선스/보안 현황을 자동 리포트로 대체합니다.")

client = get_graph_client()

st.subheader("📦 라이선스 사용률")
lic_df = audit.license_utilization_report(client)
st.dataframe(lic_df, width="stretch", hide_index=True)
st.download_button(
    "CSV 다운로드", lic_df.to_csv(index=False).encode("utf-8-sig"), "license_report.csv", "text/csv"
)

st.divider()
st.subheader("🔐 MFA 미등록 계정")
mfa_df = audit.mfa_compliance_report(client)
if mfa_df.empty:
    st.success("모든 계정이 MFA를 등록했습니다.")
else:
    st.warning(f"{len(mfa_df)}개 계정이 MFA 미등록 상태입니다.")
    st.dataframe(mfa_df, width="stretch", hide_index=True)
    st.download_button(
        "CSV 다운로드",
        mfa_df.to_csv(index=False).encode("utf-8-sig"),
        "mfa_report.csv",
        "text/csv",
        key="mfa_csv",
    )

st.divider()
days = st.slider("미로그인 기준 일수", 30, 180, config.INACTIVE_DAYS_THRESHOLD, step=15)
st.subheader(f"🕒 {days}일 이상 미로그인 계정")
inactive_df = audit.inactive_accounts_report(client, days=days)
if inactive_df.empty:
    st.success(f"{days}일 이상 미로그인 계정이 없습니다.")
else:
    st.warning(f"{len(inactive_df)}개 계정이 {days}일 이상 로그인하지 않았습니다.")
    st.dataframe(inactive_df, width="stretch", hide_index=True)
    st.download_button(
        "CSV 다운로드",
        inactive_df.to_csv(index=False).encode("utf-8-sig"),
        "inactive_report.csv",
        "text/csv",
        key="inactive_csv",
    )

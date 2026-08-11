"""라이선스 사용 현황 및 보안 감사 리포트.

매달 수동으로 사용자 목록을 엑셀로 내려받아 확인하던 작업을 대체한다:
- 구매했지만 배정되지 않은 라이선스(비용 낭비 후보)
- MFA 미등록 계정(보안 위험)
- 장기 미로그인 계정(정리 후보)
"""

from datetime import datetime, timedelta, timezone

import pandas as pd

from graph.client import GraphClient


def license_utilization_report(client: GraphClient) -> pd.DataFrame:
    licenses = client.list_licenses()
    rows = [
        {
            "라이선스": lic["displayName"],
            "총 보유": lic["totalUnits"],
            "사용 중": lic["consumedUnits"],
            "미사용": lic["totalUnits"] - lic["consumedUnits"],
            "사용률(%)": round(lic["consumedUnits"] / lic["totalUnits"] * 100, 1)
            if lic["totalUnits"]
            else 0,
        }
        for lic in licenses
    ]
    return pd.DataFrame(rows)


def mfa_compliance_report(client: GraphClient) -> pd.DataFrame:
    users = client.list_users()
    rows = [
        {
            "이름": u["displayName"],
            "UPN": u["userPrincipalName"],
            "부서": u.get("department", ""),
            "MFA 등록": "등록됨" if u.get("mfaRegistered") else "미등록",
            "계정 상태": "활성" if u.get("accountEnabled") else "비활성",
        }
        for u in users
        if not u.get("mfaRegistered")
    ]
    return pd.DataFrame(rows)


def inactive_accounts_report(client: GraphClient, days: int = 90) -> pd.DataFrame:
    users = client.list_users()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = []
    for u in users:
        last_sign_in = u.get("lastSignIn")
        if not last_sign_in:
            continue
        last_dt = datetime.fromisoformat(last_sign_in.replace("Z", "+00:00"))
        if last_dt < cutoff:
            rows.append(
                {
                    "이름": u["displayName"],
                    "UPN": u["userPrincipalName"],
                    "부서": u.get("department", ""),
                    "마지막 로그인": last_dt.strftime("%Y-%m-%d"),
                    "경과일": (datetime.now(timezone.utc) - last_dt).days,
                    "할당 라이선스": ", ".join(u.get("assignedLicenses", [])) or "-",
                }
            )
    return pd.DataFrame(rows).sort_values("경과일", ascending=False) if rows else pd.DataFrame(rows)

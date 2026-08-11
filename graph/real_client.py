from typing import Optional

import msal
import requests

import config
from graph.client import GraphClient

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPE = ["https://graph.microsoft.com/.default"]

# 필요한 Application 권한 (Entra ID 앱 등록 > API 권한에서 관리자 동의 필요):
#   User.ReadWrite.All, Group.ReadWrite.All, Directory.Read.All,
#   Reports.Read.All (MFA/로그인 활동 조회용)


class RealGraphClient(GraphClient):
    """client credentials 플로우로 실제 Microsoft Graph API를 호출하는 구현체.

    MockGraphClient와 동일한 인터페이스를 구현하므로 modules/* 코드는
    수정 없이 그대로 실제 테넌트에 대해 동작한다. config.USE_MOCK_GRAPH=false 로
    전환하면 활성화된다.
    """

    def __init__(self):
        self._app = msal.ConfidentialClientApplication(
            client_id=config.GRAPH_CLIENT_ID,
            client_credential=config.GRAPH_CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{config.GRAPH_TENANT_ID}",
        )
        self._group_cache: dict[str, str] = {}

    def _headers(self) -> dict:
        result = self._app.acquire_token_silent(SCOPE, account=None)
        if not result:
            result = self._app.acquire_token_for_client(scopes=SCOPE)
        if "access_token" not in result:
            raise RuntimeError(f"Graph 인증 실패: {result.get('error_description')}")
        return {"Authorization": f"Bearer {result['access_token']}"}

    def list_users(self) -> list[dict]:
        fields = "id,displayName,userPrincipalName,department,jobTitle,accountEnabled,assignedLicenses,signInActivity"
        resp = requests.get(
            f"{GRAPH_BASE}/users?$select={fields}", headers=self._headers(), timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("value", [])

    def get_user(self, user_id: str) -> Optional[dict]:
        resp = requests.get(f"{GRAPH_BASE}/users/{user_id}", headers=self._headers(), timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def create_user(self, profile: dict) -> dict:
        upn = f"{profile['mailNickname']}@{config.GRAPH_TENANT_ID}"
        body = {
            "accountEnabled": True,
            "displayName": profile["displayName"],
            "mailNickname": profile["mailNickname"],
            "userPrincipalName": upn,
            "department": profile.get("department", ""),
            "jobTitle": profile.get("jobTitle", ""),
            "passwordProfile": {
                "forceChangePasswordNextSignIn": True,
                "password": profile["temp_password"],
            },
        }
        resp = requests.post(f"{GRAPH_BASE}/users", headers=self._headers(), json=body, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def assign_license(self, user_id: str, sku_id: str) -> None:
        body = {"addLicenses": [{"skuId": sku_id}], "removeLicenses": []}
        resp = requests.post(
            f"{GRAPH_BASE}/users/{user_id}/assignLicense",
            headers=self._headers(),
            json=body,
            timeout=30,
        )
        resp.raise_for_status()

    def _group_id(self, group_name: str) -> str:
        if group_name in self._group_cache:
            return self._group_cache[group_name]
        resp = requests.get(
            f"{GRAPH_BASE}/groups?$filter=displayName eq '{group_name}'",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        values = resp.json().get("value", [])
        if not values:
            raise ValueError(f"Group '{group_name}' not found")
        group_id = values[0]["id"]
        self._group_cache[group_name] = group_id
        return group_id

    def add_user_to_group(self, user_id: str, group_name: str) -> None:
        group_id = self._group_id(group_name)
        body = {"@odata.id": f"{GRAPH_BASE}/directoryObjects/{user_id}"}
        resp = requests.post(
            f"{GRAPH_BASE}/groups/{group_id}/members/$ref",
            headers=self._headers(),
            json=body,
            timeout=30,
        )
        resp.raise_for_status()

    def disable_user(self, user_id: str) -> None:
        resp = requests.patch(
            f"{GRAPH_BASE}/users/{user_id}",
            headers=self._headers(),
            json={"accountEnabled": False},
            timeout=30,
        )
        resp.raise_for_status()

    def revoke_sign_in_sessions(self, user_id: str) -> None:
        resp = requests.post(
            f"{GRAPH_BASE}/users/{user_id}/revokeSignInSessions",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()

    def list_licenses(self) -> list[dict]:
        resp = requests.get(f"{GRAPH_BASE}/subscribedSkus", headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def list_groups(self) -> list[str]:
        resp = requests.get(
            f"{GRAPH_BASE}/groups?$select=displayName", headers=self._headers(), timeout=30
        )
        resp.raise_for_status()
        return [g["displayName"] for g in resp.json().get("value", [])]

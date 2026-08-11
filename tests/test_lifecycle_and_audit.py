"""목업 Graph 클라이언트 기준 핵심 로직 검증.

실제 테넌트 없이도 온보딩/오프보딩/감사 리포트 로직을 pytest로 검증한다.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["USE_MOCK_GRAPH"] = "true"

import pytest

from graph.client import get_graph_client
from modules import audit, lifecycle


@pytest.fixture
def client():
    c = get_graph_client()
    c.reset()
    yield c
    c.reset()


def test_onboard_creates_user_with_license_and_groups(client):
    log = lifecycle.onboard_user(
        client,
        {
            "displayName": "테스트 사용자",
            "mailNickname": "test.user",
            "department": "IT",
            "jobTitle": "인턴",
            "license_sku": "ENTERPRISEPACK",
            "groups": ["All Staff", "IT"],
        },
    )
    assert all(entry["status"] in ("성공", "완료") for entry in log)

    users = client.list_users()
    created = next(u for u in users if u["userPrincipalName"].startswith("test.user@"))
    assert "ENTERPRISEPACK" in created["assignedLicenses"]
    assert set(["All Staff", "IT"]).issubset(created["groups"])


def test_offboard_disables_account(client):
    user_id = client.list_users()[0]["id"]
    lifecycle.offboard_user(client, user_id)
    assert client.get_user(user_id)["accountEnabled"] is False


def test_mfa_report_only_lists_unregistered(client):
    df = audit.mfa_compliance_report(client)
    assert not df.empty
    assert (df["MFA 등록"] == "미등록").all()


def test_inactive_report_respects_threshold(client):
    df = audit.inactive_accounts_report(client, days=9999)
    assert df.empty

    df = audit.inactive_accounts_report(client, days=1)
    assert not df.empty

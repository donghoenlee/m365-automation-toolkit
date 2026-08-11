import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import Optional

import config
from graph.client import GraphClient

SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seed_db.json")


class MockGraphClient(GraphClient):
    """Graph API 응답 형태를 흉내 내는 로컬 JSON 기반 클라이언트.

    실제 테넌트 없이도 온보딩/오프보딩/감사 로직 전체를 시연할 수 있도록
    상태를 data/mock_db.json 파일에 저장한다 (앱 재시작 후에도 유지됨).
    """

    def __init__(self):
        self._db_path = config.MOCK_DB_PATH
        if not os.path.exists(self._db_path):
            shutil.copyfile(SEED_PATH, self._db_path)
        self._load()

    def _load(self):
        with open(self._db_path, encoding="utf-8") as f:
            self._db = json.load(f)

    def _save(self):
        with open(self._db_path, "w", encoding="utf-8") as f:
            json.dump(self._db, f, ensure_ascii=False, indent=2)

    def reset(self):
        shutil.copyfile(SEED_PATH, self._db_path)
        self._load()

    def _find_user(self, user_id: str) -> Optional[dict]:
        return next((u for u in self._db["users"] if u["id"] == user_id), None)

    def list_users(self) -> list[dict]:
        return list(self._db["users"])

    def get_user(self, user_id: str) -> Optional[dict]:
        return self._find_user(user_id)

    def create_user(self, profile: dict) -> dict:
        user_id = f"u{uuid.uuid4().hex[:8]}"
        upn = f"{profile['mailNickname']}@{self._db['tenant_domain']}"
        user = {
            "id": user_id,
            "displayName": profile["displayName"],
            "userPrincipalName": upn,
            "department": profile.get("department", ""),
            "jobTitle": profile.get("jobTitle", ""),
            "accountEnabled": True,
            "assignedLicenses": [],
            "groups": [],
            "mfaRegistered": False,
            "lastSignIn": None,
            "createdDateTime": datetime.now(timezone.utc).isoformat(),
        }
        self._db["users"].append(user)
        self._save()
        return user

    def assign_license(self, user_id: str, sku_part_number: str) -> None:
        user = self._find_user(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        if sku_part_number not in user["assignedLicenses"]:
            user["assignedLicenses"].append(sku_part_number)
        for lic in self._db["licenses"]:
            if lic["skuPartNumber"] == sku_part_number:
                lic["consumedUnits"] = min(lic["consumedUnits"] + 1, lic["totalUnits"])
        self._save()

    def add_user_to_group(self, user_id: str, group_name: str) -> None:
        user = self._find_user(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        if group_name not in user["groups"]:
            user["groups"].append(group_name)
        self._save()

    def disable_user(self, user_id: str) -> None:
        user = self._find_user(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        user["accountEnabled"] = False
        self._save()

    def revoke_sign_in_sessions(self, user_id: str) -> None:
        # 목업에서는 별도 상태가 없으므로 감사 로그만 남긴다.
        self._db["audit_log"].append(
            {
                "action": "revoke_sign_in_sessions",
                "userId": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save()

    def list_licenses(self) -> list[dict]:
        return list(self._db["licenses"])

    def list_groups(self) -> list[str]:
        return list(self._db["groups"])

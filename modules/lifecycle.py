"""신규 입사자 온보딩 / 퇴사자 오프보딩 자동화.

수작업으로 하면 IT 담당자가 여러 관리 포털(Entra ID, Exchange, Teams)을
오가며 5~10분씩 걸리는 계정 생성·라이선스 할당·그룹 추가 절차를
한 번의 호출로 처리하고, 각 단계의 성공/실패를 로그로 남긴다.
"""

import secrets
import string

from graph.client import GraphClient


def _temp_password() -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(14))


def onboard_user(client: GraphClient, profile: dict) -> list[dict]:
    """profile: displayName, mailNickname, department, jobTitle,
    license_sku(str), groups(list[str])
    """
    log = []

    try:
        profile = {**profile, "temp_password": _temp_password()}
        user = client.create_user(profile)
        log.append({"step": "계정 생성", "status": "성공", "detail": user["userPrincipalName"]})
    except Exception as e:
        log.append({"step": "계정 생성", "status": "실패", "detail": str(e)})
        return log

    license_sku = profile.get("license_sku")
    if license_sku:
        try:
            client.assign_license(user["id"], license_sku)
            log.append({"step": "라이선스 할당", "status": "성공", "detail": license_sku})
        except Exception as e:
            log.append({"step": "라이선스 할당", "status": "실패", "detail": str(e)})

    for group in profile.get("groups", []):
        try:
            client.add_user_to_group(user["id"], group)
            log.append({"step": f"그룹 추가 ({group})", "status": "성공", "detail": group})
        except Exception as e:
            log.append({"step": f"그룹 추가 ({group})", "status": "실패", "detail": str(e)})

    log.append(
        {
            "step": "임시 비밀번호",
            "status": "완료",
            "detail": "최초 로그인 시 변경 필요 (안전 채널로 별도 전달)",
        }
    )
    return log


def offboard_user(client: GraphClient, user_id: str) -> list[dict]:
    log = []

    try:
        client.disable_user(user_id)
        log.append({"step": "계정 비활성화", "status": "성공", "detail": user_id})
    except Exception as e:
        log.append({"step": "계정 비활성화", "status": "실패", "detail": str(e)})

    try:
        client.revoke_sign_in_sessions(user_id)
        log.append({"step": "로그인 세션 강제 종료", "status": "성공", "detail": "-"})
    except Exception as e:
        log.append({"step": "로그인 세션 강제 종료", "status": "실패", "detail": str(e)})

    log.append(
        {
            "step": "메일함/OneDrive 보존",
            "status": "안내",
            "detail": "규정에 따라 30일 보존 후 라이선스 회수 처리 필요 (수동 확인 권장)",
        }
    )
    return log

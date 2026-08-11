from abc import ABC, abstractmethod
from typing import Optional


class GraphClient(ABC):
    """Microsoft Graph 작업에 대한 공통 인터페이스.

    MockGraphClient(로컬 JSON)와 RealGraphClient(실제 Graph API)가
    동일한 시그니처를 구현하므로, 상위 모듈(modules/*)은 어떤 구현체가
    붙어 있는지 신경 쓰지 않고 그대로 재사용된다.
    """

    @abstractmethod
    def list_users(self) -> list[dict]: ...

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[dict]: ...

    @abstractmethod
    def create_user(self, profile: dict) -> dict: ...

    @abstractmethod
    def assign_license(self, user_id: str, sku_part_number: str) -> None: ...

    @abstractmethod
    def add_user_to_group(self, user_id: str, group_name: str) -> None: ...

    @abstractmethod
    def disable_user(self, user_id: str) -> None: ...

    @abstractmethod
    def revoke_sign_in_sessions(self, user_id: str) -> None: ...

    @abstractmethod
    def list_licenses(self) -> list[dict]: ...

    @abstractmethod
    def list_groups(self) -> list[str]: ...


def get_graph_client() -> GraphClient:
    import config

    if config.USE_MOCK_GRAPH:
        from graph.mock_client import MockGraphClient

        return MockGraphClient()

    from graph.real_client import RealGraphClient

    return RealGraphClient()

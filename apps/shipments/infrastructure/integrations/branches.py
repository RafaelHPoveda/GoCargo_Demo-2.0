from typing import Protocol
from uuid import UUID

from apps.branches.application.dto import BranchDtoInfo as LocalBranchDtoInfo
from apps.shipments.application.dto import BranchDtoInfo


class BranchReader(Protocol):
    def get_info(self, branch_id: UUID) -> LocalBranchDtoInfo | None: ...


class LocalBranchChecker:
    def __init__(self, service: BranchReader) -> None:
        self._service = service

    def get_branch_info(self, branch_id: UUID) -> BranchDtoInfo | None:
        branch = self._service.get_info(branch_id)
        if branch is None:
            return None
        return BranchDtoInfo(
            id=branch.id,
            name=branch.name,
            is_active=branch.is_active,
            max_weight_kg=branch.max_weight_kg,
        )

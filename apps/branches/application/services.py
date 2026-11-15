from dataclasses import replace
from uuid import UUID

from apps.branches.application.dto import (
    BranchDto,
    BranchDtoCreate,
    BranchDtoInfo,
    BranchDtoUpdate,
)
from apps.branches.application.exceptions import BranchNotFoundError
from apps.branches.application.ports import IBranchRepository
from apps.branches.domain.entities import Branch


class BranchService:
    def __init__(self, repository: IBranchRepository) -> None:
        self._repository = repository

    def create(self, data: BranchDtoCreate) -> BranchDto:
        branch = Branch(
            name=data.name,
            city=data.city,
            max_weight_kg=data.max_weight_kg,
            is_active=data.is_active,
        )
        saved = self._repository.create(branch)
        return BranchDto.from_entity(saved)

    def get_all(self) -> list[BranchDto]:
        return [BranchDto.from_entity(branch) for branch in self._repository.get_all()]

    def update(self, branch_id: UUID, data: BranchDtoUpdate) -> BranchDto:
        branch = self._repository.get_by_id(branch_id)
        if branch is None:
            raise BranchNotFoundError("La sucursal no existe.")
        changes = {
            field: value
            for field in ("name", "city", "max_weight_kg", "is_active")
            if (value := getattr(data, field)) is not None
        }
        updated = replace(branch, **changes)
        saved = self._repository.update(updated)
        if saved is None:
            raise BranchNotFoundError("La sucursal no existe.")
        return BranchDto.from_entity(saved)

    def get_info(self, branch_id: UUID) -> BranchDtoInfo | None:
        branch = self._repository.get_by_id(branch_id)
        if branch is None:
            return None
        return BranchDtoInfo(
            id=branch.id,
            name=branch.name,
            is_active=branch.is_active,
            max_weight_kg=branch.max_weight_kg,
        )

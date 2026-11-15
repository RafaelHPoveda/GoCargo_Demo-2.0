from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from apps.branches.domain.entities import Branch
from core.mapping import object_mapper


@dataclass(frozen=True, kw_only=True)
class BranchDtoCreate:
    name: str
    city: str
    max_weight_kg: Decimal
    is_active: bool = True


@dataclass(frozen=True, kw_only=True)
class BranchDtoUpdate:
    """None indica un campo no enviado; los valores nulos se rechazan en HTTP."""

    name: str | None = None
    city: str | None = None
    max_weight_kg: Decimal | None = None
    is_active: bool | None = None


@dataclass(frozen=True, kw_only=True)
class BranchDto:
    id: UUID
    name: str
    city: str
    max_weight_kg: Decimal
    is_active: bool

    @classmethod
    def from_entity(cls, branch: Branch) -> "BranchDto":
        return object_mapper.to(cls).map(branch)


@dataclass(frozen=True, kw_only=True)
class BranchDtoInfo:
    id: UUID
    name: str
    is_active: bool
    max_weight_kg: Decimal

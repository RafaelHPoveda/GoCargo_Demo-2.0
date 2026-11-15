from typing import Protocol

from apps.branches.domain.entities import Branch
from core.ports import IBaseRepository


class IBranchRepository(IBaseRepository[Branch], Protocol):
    """Persistencia de sucursales; hereda las operaciones del contrato base."""

from typing import Protocol
from uuid import UUID

from apps.shipments.application.dto import BranchDtoInfo, CountryDto
from apps.shipments.domain.entities import Shipment
from core.ports import IBaseRepository


class IBranchChecker(Protocol):
    def get_branch_info(self, branch_id: UUID) -> BranchDtoInfo | None: ...


class ICountryCatalog(Protocol):
    def get_country(self, code: str) -> CountryDto | None:
        """Devuelve datos, None por ausencia confirmada o lanza un fallo de catálogo."""
        ...


class IShipmentRepository(IBaseRepository[Shipment], Protocol):
    """Persistencia de envios; hereda las operaciones del contrato base."""

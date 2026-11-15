from contextlib import AbstractContextManager
from uuid import UUID

from apps.shipments.application.dto import ShipmentDto, ShipmentDtoCreate
from apps.shipments.application.exceptions import (
    BranchCapacityExceededError,
    BranchInactiveError,
    BranchNotFoundError,
    CountryNotFoundError,
    ShipmentNotFoundError,
)
from apps.shipments.application.ports import IBranchChecker, ICountryCatalog, IShipmentRepository
from apps.shipments.domain.entities import Shipment
from apps.shipments.domain.exceptions import InvalidShipmentError
from apps.shipments.domain.value_objects import PackageWeight


class ShipmentService:
    def __init__(
        self,
        repository: IShipmentRepository,
        branch_checker: IBranchChecker,
        country_catalog: ICountryCatalog,
        unit_of_work: AbstractContextManager,
    ) -> None:
        self._repository = repository
        self._branch_checker = branch_checker
        self._country_catalog = country_catalog
        self._unit_of_work = unit_of_work

    def get_all(self) -> list[ShipmentDto]:
        return [ShipmentDto.from_entity(entity) for entity in self._repository.get_all()]

    def get_by_id(self, shipment_id: UUID) -> ShipmentDto:
        shipment = self._repository.get_by_id(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError("El envío no existe.")
        return ShipmentDto.from_entity(shipment)

    def create(self, data: ShipmentDtoCreate) -> ShipmentDto:
        weight = PackageWeight(data.weight_kg)
        code = data.destination_country_code.strip().upper()
        if len(code) != 2 or not code.isascii() or not code.isalpha():
            raise InvalidShipmentError("El país debe tener un código de dos letras.")

        branch = self._branch_checker.get_branch_info(data.origin_branch_id)
        if branch is None:
            raise BranchNotFoundError("La sucursal no existe.")
        if not branch.is_active:
            raise BranchInactiveError("La sucursal está inactiva.")
        if weight.kg > branch.max_weight_kg:
            raise BranchCapacityExceededError("El peso supera la capacidad de la sucursal.")

        country = self._country_catalog.get_country(code)
        if country is None:
            raise CountryNotFoundError("El país no existe en el catálogo.")

        with self._unit_of_work:
            shipment = Shipment(
                origin_branch_id=branch.id,
                origin_branch_name=branch.name,
                description=data.description,
                weight=weight,
                destination_country_code=country.code,
                destination_country_name=country.name,
                currency=country.currency,
            )
            saved = self._repository.create(shipment)
            result = ShipmentDto.from_entity(saved)
        return result

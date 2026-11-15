from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from apps.shipments.domain.entities import Shipment
from core.mapping import object_mapper


@dataclass(frozen=True, kw_only=True)
class BranchDtoInfo:
    id: UUID
    name: str
    is_active: bool
    max_weight_kg: Decimal


@dataclass(frozen=True, kw_only=True)
class CountryDto:
    code: str
    name: str
    currency: str


@dataclass(frozen=True, kw_only=True)
class ShipmentDtoCreate:
    origin_branch_id: UUID
    description: str
    weight_kg: Decimal
    destination_country_code: str


@dataclass(frozen=True, kw_only=True)
class ShipmentDto:
    id: UUID
    origin_branch_id: UUID
    origin_branch_name: str
    description: str
    weight_kg: Decimal
    destination_country_code: str
    destination_country_name: str
    currency: str
    status: str

    @classmethod
    def from_entity(cls, shipment: Shipment) -> "ShipmentDto":
        return object_mapper.to(cls).map(shipment, fields_mapping={"weight_kg": shipment.weight.kg})

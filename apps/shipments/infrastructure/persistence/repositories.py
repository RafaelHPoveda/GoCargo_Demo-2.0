from apps.shipments.domain.entities import Shipment
from apps.shipments.domain.value_objects import PackageWeight
from apps.shipments.infrastructure.persistence.models import ShipmentModel
from core.repositories import BaseRepository


class DjangoShipmentRepository(BaseRepository[Shipment, ShipmentModel]):
    def __init__(self, db_alias: str = "default") -> None:
        super().__init__(
            ShipmentModel,
            Shipment,
            db_alias,
            model_fields=lambda entity: {"weight_kg": entity.weight.kg},
            domain_fields=lambda model: {"weight": PackageWeight(model.weight_kg)},
        )

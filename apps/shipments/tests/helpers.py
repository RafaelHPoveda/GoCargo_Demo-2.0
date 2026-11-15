from decimal import Decimal
from uuid import uuid4

from apps.shipments.domain.entities import Shipment
from apps.shipments.domain.value_objects import PackageWeight


def make_shipment() -> Shipment:
    return Shipment(
        origin_branch_id=uuid4(),
        origin_branch_name="Sucursal histórica",
        description="Documentos",
        weight=PackageWeight(Decimal("2.50")),
        destination_country_code="CR",
        destination_country_name="Costa Rica",
        currency="CRC",
    )

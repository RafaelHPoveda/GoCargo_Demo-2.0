from rest_framework import serializers
from rest_framework_dataclasses.serializers import DataclassSerializer

from apps.shipments.application.dto import ShipmentDto, ShipmentDtoCreate


class ShipmentDtoCreateSerializer(DataclassSerializer[ShipmentDtoCreate]):
    destination_country_code = serializers.RegexField(r"^[A-Za-z]{2}$")

    class Meta:
        dataclass = ShipmentDtoCreate
        extra_kwargs = {
            "description": {"max_length": 500},
            "weight_kg": {"max_digits": 8, "decimal_places": 2},
        }

    def validate_destination_country_code(self, value):
        return value.strip().upper()


class ShipmentDtoSerializer(DataclassSerializer[ShipmentDto]):
    class Meta:
        dataclass = ShipmentDto
        extra_kwargs = {"weight_kg": {"max_digits": 8, "decimal_places": 2}}

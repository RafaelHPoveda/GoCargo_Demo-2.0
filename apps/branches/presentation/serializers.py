from rest_framework import serializers
from rest_framework_dataclasses.serializers import DataclassSerializer

from apps.branches.application.dto import BranchDto, BranchDtoCreate, BranchDtoUpdate

BRANCH_HTTP_FIELDS = {
    "name": {"max_length": 200},
    "city": {"max_length": 120},
    "max_weight_kg": {"max_digits": 8, "decimal_places": 2},
}


class BranchDtoSerializer(DataclassSerializer[BranchDto]):
    class Meta:
        dataclass = BranchDto
        extra_kwargs = BRANCH_HTTP_FIELDS


class BranchDtoCreateSerializer(DataclassSerializer[BranchDtoCreate]):
    class Meta:
        dataclass = BranchDtoCreate
        extra_kwargs = BRANCH_HTTP_FIELDS


class BranchDtoUpdateSerializer(DataclassSerializer[BranchDtoUpdate]):
    class Meta:
        dataclass = BranchDtoUpdate
        extra_kwargs = {
            name: {**options, "required": True, "allow_null": False}
            for name, options in {**BRANCH_HTTP_FIELDS, "is_active": {}}.items()
        }

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({"unknown_fields": sorted(unknown)})
        if not self.initial_data:
            raise serializers.ValidationError("Envia al menos un campo para actualizar.")
        return attrs

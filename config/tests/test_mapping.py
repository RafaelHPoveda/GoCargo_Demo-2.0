from dataclasses import fields
from decimal import Decimal

from django.test import SimpleTestCase

from apps.branches.application.dto import BranchDto, BranchDtoCreate, BranchDtoUpdate
from apps.branches.domain.entities import Branch
from apps.branches.domain.exceptions import InvalidBranchNameError
from apps.branches.infrastructure.persistence.repositories import DjangoBranchRepository
from apps.branches.presentation.serializers import (
    BranchDtoCreateSerializer,
    BranchDtoUpdateSerializer,
)
from apps.shipments.application.dto import ShipmentDto
from apps.shipments.infrastructure.persistence.repositories import DjangoShipmentRepository
from apps.shipments.tests.helpers import make_shipment


class AutomaticMappingTests(SimpleTestCase):
    def test_branch_round_trip_and_dto_without_orm_fields(self):
        entity = Branch(name="Managua", city="Managua", max_weight_kg=Decimal("25.25"))
        model = DjangoBranchRepository()._mapper.to_model(entity)
        self.assertEqual(DjangoBranchRepository()._mapper.to_domain(model), entity)
        dto = BranchDto.from_entity(entity)
        self.assertEqual(dto.id, entity.id)
        self.assertEqual(dto.max_weight_kg, Decimal("25.25"))
        self.assertEqual(set(vars(dto)), {field.name for field in fields(BranchDto)})

    def test_weight_is_flattened_for_storage_and_dto_and_restored_for_domain(self):
        entity = make_shipment()
        model = DjangoShipmentRepository()._mapper.to_model(entity)
        self.assertEqual(model.weight_kg, entity.weight.kg)
        restored = DjangoShipmentRepository()._mapper.to_domain(model)
        self.assertEqual(restored, entity)
        self.assertEqual(ShipmentDto.from_entity(entity).weight_kg, entity.weight.kg)

    def test_automatic_mapping_keeps_domain_constructor_validation(self):
        entity = Branch(name="Managua", city="Managua", max_weight_kg=Decimal("25"))
        model = DjangoBranchRepository()._mapper.to_model(entity)
        model.name = ""
        with self.assertRaises(InvalidBranchNameError):
            DjangoBranchRepository()._mapper.to_domain(model)

    def test_serializer_returns_create_dto_instead_of_dictionary(self):
        serializer = BranchDtoCreateSerializer(
            data={"name": "Managua", "city": "Managua", "max_weight_kg": "25.00"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIsInstance(serializer.validated_data, BranchDtoCreate)
        self.assertTrue(serializer.validated_data.is_active)
        self.assertIsInstance(serializer.validated_data.max_weight_kg, Decimal)

    def test_partial_update_retains_false_and_defaults_omitted_fields(self):
        serializer = BranchDtoUpdateSerializer(data={"is_active": False}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIsInstance(serializer.validated_data, BranchDtoUpdate)
        self.assertIs(serializer.validated_data.is_active, False)
        self.assertIsNone(serializer.validated_data.name)

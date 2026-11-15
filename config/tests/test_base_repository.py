from dataclasses import replace
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.db import DatabaseError, IntegrityError, transaction
from django.test import TestCase

from apps.branches.domain.entities import Branch
from apps.branches.infrastructure.persistence.repositories import DjangoBranchRepository
from apps.shipments.infrastructure.persistence.repositories import DjangoShipmentRepository
from apps.shipments.tests.helpers import make_shipment
from core.exceptions import RepositoryConflictError, RepositoryError


class BaseRepositoryTests(TestCase):
    def setUp(self):
        self.cases = [
            (
                DjangoBranchRepository(),
                Branch(name="Managua", city="Managua", max_weight_kg=Decimal("25.00")),
                {"city": "Leon", "is_active": False},
            ),
            (DjangoShipmentRepository(), make_shipment(), {"description": "Contenido actualizado"}),
        ]

    def test_create_and_get_by_id_preserve_domain_entities(self):
        for repository, entity, _ in self.cases:
            with self.subTest(model=repository._model):
                self.assertEqual(repository.create(entity), entity)
                self.assertEqual(repository.get_by_id(entity.id), entity)

    def test_get_all_returns_empty_list_then_entities_in_stable_order(self):
        for repository, entity, _ in self.cases:
            with self.subTest(model=repository._model):
                self.assertEqual(repository.get_all(), [])
                second = replace(entity, id=uuid4())
                repository.create(entity)
                repository.create(second)
                self.assertEqual(repository.get_all(), sorted([entity, second], key=lambda e: e.id))

    def test_get_all_preserves_branch_name_order(self):
        repository = self.cases[0][0]
        for name in ("Zeta", "Alfa"):
            repository.create(Branch(name=name, city="Managua", max_weight_kg=Decimal("25.00")))
        self.assertEqual([branch.name for branch in repository.get_all()], ["Alfa", "Zeta"])

    def test_duplicate_create_is_conflict_and_does_not_overwrite(self):
        for repository, entity, changes in self.cases:
            with self.subTest(model=repository._model):
                repository.create(entity)
                with self.assertRaises(RepositoryConflictError), transaction.atomic():
                    repository.create(replace(entity, **changes))
                self.assertEqual(repository.get_by_id(entity.id), entity)

    def test_update_changes_existing_entity_and_preserves_identity(self):
        for repository, entity, changes in self.cases:
            with self.subTest(model=repository._model):
                repository.create(entity)
                updated = replace(entity, **changes)
                self.assertEqual(repository.update(updated), updated)
                self.assertEqual(repository.get_by_id(entity.id), updated)
                self.assertEqual(len(repository.get_all()), 1)

    def test_update_unchanged_entity_still_returns_entity(self):
        for repository, entity, _ in self.cases:
            with self.subTest(model=repository._model):
                repository.create(entity)
                self.assertEqual(repository.update(entity), entity)

    def test_update_missing_entity_never_inserts(self):
        for repository, entity, _ in self.cases:
            with self.subTest(model=repository._model):
                self.assertIsNone(repository.update(entity))
                self.assertIsNone(repository.get_by_id(entity.id))
                self.assertEqual(repository.get_all(), [])

    def test_delete_returns_boolean_and_leaves_other_records(self):
        for repository, entity, _ in self.cases:
            with self.subTest(model=repository._model):
                other = replace(entity, id=uuid4())
                repository.create(entity)
                repository.create(other)
                self.assertIs(repository.delete(entity.id), True)
                self.assertIs(repository.delete(entity.id), False)
                self.assertIsNone(repository.get_by_id(entity.id))
                self.assertEqual(repository.get_by_id(other.id), other)

    def test_is_exist_returns_boolean_without_mapping(self):
        for repository, entity, _ in self.cases:
            with self.subTest(model=repository._model):
                self.assertIs(repository.is_exist(entity.id), False)
                repository.create(entity)
                with patch.object(repository._mapper, "to_domain", side_effect=AssertionError):
                    with self.assertNumQueries(1):
                        self.assertIs(repository.is_exist(entity.id), True)
                repository.delete(entity.id)
                self.assertIs(repository.is_exist(entity.id), False)

    def test_missing_get_by_id_returns_none(self):
        for repository, entity, _ in self.cases:
            with self.subTest(model=repository._model):
                self.assertIsNone(repository.get_by_id(entity.id))

    def test_update_and_delete_can_be_rolled_back_together(self):
        for repository, entity, changes in self.cases:
            with self.subTest(model=repository._model):
                repository.create(entity)
                with self.assertRaises(RuntimeError), transaction.atomic():
                    repository.update(replace(entity, **changes))
                    repository.delete(entity.id)
                    raise RuntimeError("Rollback")
                self.assertEqual(repository.get_by_id(entity.id), entity)

    def test_database_errors_are_translated_for_reads_and_writes(self):
        for repository, entity, _ in self.cases:
            operations = [
                lambda: repository.get_all(),
                lambda: repository.get_by_id(entity.id),
                lambda: repository.update(entity),
                lambda: repository.delete(entity.id),
                lambda: repository.is_exist(entity.id),
            ]
            for operation in operations:
                with self.subTest(model=repository._model, operation=operation):
                    with patch.object(
                        repository._model._default_manager,
                        "using",
                        side_effect=DatabaseError("private"),
                    ):
                        with self.assertRaises(RepositoryError):
                            operation()
            with patch.object(repository._model, "save", side_effect=DatabaseError("private")):
                with self.assertRaises(RepositoryError):
                    repository.create(entity)

    def test_integrity_errors_are_conflicts_for_update_and_delete(self):
        for repository, entity, _ in self.cases:
            for operation in (
                lambda: repository.update(entity),
                lambda: repository.delete(entity.id),
            ):
                with self.subTest(model=repository._model):
                    with patch.object(
                        repository._model._default_manager,
                        "using",
                        side_effect=IntegrityError("constraint"),
                    ):
                        with self.assertRaises(RepositoryConflictError):
                            operation()

    def test_failed_update_constraint_does_not_destroy_previous_data(self):
        repository, entity, _ = self.cases[0]
        repository.create(entity)
        invalid_model = repository._mapper.to_model(entity)
        invalid_model.max_weight_kg = Decimal("-1.00")
        with patch.object(repository._mapper, "to_model", return_value=invalid_model):
            with self.assertRaises(RepositoryConflictError), transaction.atomic():
                repository.update(entity)
        self.assertEqual(repository.get_by_id(entity.id), entity)

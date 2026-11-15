from django.db.transaction import atomic
from django.test import TransactionTestCase

from apps.shipments.infrastructure.persistence.repositories import DjangoShipmentRepository
from apps.shipments.models import ShipmentModel
from apps.shipments.tests.helpers import make_shipment


class ShipmentPersistenceTests(TransactionTestCase):
    def setUp(self):
        self.repository = DjangoShipmentRepository()

    def test_commit_and_round_trip_preserve_snapshots(self):
        shipment = make_shipment()
        with atomic():
            self.repository.create(shipment)
        self.assertEqual(self.repository.get_by_id(shipment.id), shipment)
        self.assertEqual(ShipmentModel.objects.count(), 1)

    def test_exception_rolls_back_insert(self):
        shipment = make_shipment()
        with self.assertRaises(RuntimeError):
            with atomic():
                self.repository.create(shipment)
                raise RuntimeError("Fallo después de insertar")
        self.assertFalse(ShipmentModel.objects.exists())

    def test_same_unit_of_work_can_be_reused_after_rollback(self):
        unit_of_work = atomic()
        with self.assertRaises(RuntimeError):
            with unit_of_work:
                self.repository.create(make_shipment())
                raise RuntimeError("Fallo temporal")
        with unit_of_work:
            self.repository.create(make_shipment())
        self.assertEqual(ShipmentModel.objects.count(), 1)

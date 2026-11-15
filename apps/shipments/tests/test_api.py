from dataclasses import replace
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from rest_framework.test import APITestCase

from apps.branches.domain.entities import Branch
from apps.branches.infrastructure.persistence.repositories import DjangoBranchRepository
from apps.shipments.application.dto import CountryDto
from apps.shipments.application.exceptions import CountryCatalogUnavailableError
from apps.shipments.infrastructure.persistence.repositories import DjangoShipmentRepository
from apps.shipments.models import ShipmentModel
from apps.shipments.tests.helpers import make_shipment


class ShipmentAPITests(APITestCase):
    def setUp(self):
        self.branch = DjangoBranchRepository().create(
            Branch(name="Managua", city="Managua", max_weight_kg=Decimal("25.00"))
        )
        self.payload = {
            "origin_branch_id": str(self.branch.id),
            "description": "Documentos",
            "weight_kg": "2.50",
            "destination_country_code": "cr",
        }

    @patch("config.dependencies.build_country_catalog")
    def test_create_uses_normalized_country_and_persists(self, build_catalog):
        build_catalog.return_value.get_country.return_value = CountryDto(
            code="CR", name="Costa Rica", currency="CRC"
        )
        response = self.client.post("/api/shipments/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["destination_country_code"], "CR")
        self.assertEqual(response.data["data"]["origin_branch_name"], self.branch.name)
        self.assertEqual(ShipmentModel.objects.count(), 1)
        build_catalog.return_value.get_country.assert_called_once_with("CR")

    @patch("config.dependencies.build_country_catalog")
    def test_invalid_weight_returns_422_before_catalog(self, build_catalog):
        self.payload["weight_kg"] = "51.00"
        response = self.client.post("/api/shipments/", self.payload, format="json")
        self.assertEqual(response.status_code, 422)
        self.assertFalse(ShipmentModel.objects.exists())
        build_catalog.return_value.get_country.assert_not_called()

    @patch("config.dependencies.build_country_catalog")
    def test_missing_country_returns_404(self, build_catalog):
        build_catalog.return_value.get_country.return_value = None
        response = self.client.post("/api/shipments/", self.payload, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["meta"]["errorCode"], "country_not_found")
        self.assertFalse(ShipmentModel.objects.exists())

    @patch("config.dependencies.build_country_catalog")
    def test_catalog_failure_returns_503_without_writing(self, build_catalog):
        build_catalog.return_value.get_country.side_effect = CountryCatalogUnavailableError(
            "Catálogo no disponible."
        )
        response = self.client.post("/api/shipments/", self.payload, format="json")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(ShipmentModel.objects.exists())

    def test_invalid_uuid_returns_400(self):
        self.payload["origin_branch_id"] = "invalido"
        response = self.client.post("/api/shipments/", self.payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ShipmentModel.objects.exists())

    def test_get_shipments_returns_empty_list(self):
        response = self.client.get("/api/shipments/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    @patch("config.dependencies.build_country_catalog")
    def test_list_shipments_uses_local_snapshots_without_catalog(self, build_catalog):
        repository = DjangoShipmentRepository()
        shipments = [repository.create(make_shipment()) for _ in range(2)]
        response = self.client.get("/api/shipments/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["data"]],
            sorted(str(shipment.id) for shipment in shipments),
        )
        self.assertEqual(response.data["data"][0]["weight_kg"], "2.50")
        self.assertEqual(response.data["data"][0]["currency"], "CRC")
        build_catalog.return_value.get_country.assert_not_called()

    @patch("config.dependencies.build_country_catalog")
    def test_get_shipment_by_id_without_catalog(self, build_catalog):
        shipment = DjangoShipmentRepository().create(make_shipment())
        response = self.client.get(f"/api/shipments/{shipment.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], str(shipment.id))
        self.assertEqual(response.data["data"]["status"], "CREATED")
        build_catalog.return_value.get_country.assert_not_called()

    def test_get_missing_shipment_returns_404(self):
        response = self.client.get(f"/api/shipments/{uuid4()}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["meta"]["errorCode"], "shipment_not_found")

    def test_get_malformed_shipment_id_returns_404(self):
        self.assertEqual(self.client.get("/api/shipments/not-a-uuid/").status_code, 404)

    def test_branch_update_does_not_change_shipment_snapshots(self):
        shipment = DjangoShipmentRepository().create(
            replace(
                make_shipment(),
                origin_branch_id=self.branch.id,
                origin_branch_name=self.branch.name,
            )
        )
        response = self.client.patch(
            f"/api/branches/{self.branch.id}/",
            {"name": "Nombre nuevo", "is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        detail = self.client.get(f"/api/shipments/{shipment.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["data"]["origin_branch_name"], self.branch.name)

from unittest.mock import patch
from uuid import uuid4

from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import Throttled
from rest_framework.test import APITestCase

from config.exceptions import api_exception_handler
from core.presentation.responses import ApiResponse, ApiResponseDto

FIELDS = {"isSuccess", "errorMessages", "successMessages", "httpCode", "data", "meta"}


class ResponseContractTests(APITestCase):
    def assert_contract(self, response, *, success):
        payload = response.json()
        self.assertEqual(set(payload), FIELDS)
        self.assertIs(payload["isSuccess"], success)
        self.assertEqual(payload["httpCode"], response.status_code)
        self.assertIsInstance(payload["errorMessages"], list)
        self.assertIsInstance(payload["successMessages"], list)
        self.assertIsInstance(payload["meta"], dict)
        if success:
            self.assertEqual(payload["errorMessages"], [])
        else:
            self.assertEqual(payload["successMessages"], [])
            self.assertTrue(payload["errorMessages"])
            self.assertIsNone(payload["data"])
        return payload

    def test_create_and_list_have_the_same_envelope(self):
        created = self.client.post(
            "/api/branches/",
            {
                "name": "Managua",
                "city": "Managua",
                "max_weight_kg": "25.00",
            },
            format="json",
        )
        payload = self.assert_contract(created, success=True)
        self.assertEqual(created.status_code, 201)
        self.assertTrue(payload["successMessages"])
        self.assertNotIn("_state", payload["data"])
        listed = self.assert_contract(self.client.get("/api/branches/"), success=True)
        self.assertEqual(listed["data"][0]["id"], payload["data"]["id"])

    def test_validation_error_has_field_details(self):
        response = self.client.post("/api/branches/", {}, format="json")
        payload = self.assert_contract(response, success=False)
        self.assertEqual(response.status_code, 400)
        self.assertIn("city", payload["meta"]["validationErrors"])

    def test_business_error_has_error_code(self):
        response = self.client.get(f"/api/shipments/{uuid4()}/")
        payload = self.assert_contract(response, success=False)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(payload["meta"]["errorCode"], "shipment_not_found")

    def test_unknown_route_and_malformed_id_are_json_with_debug_on_or_off(self):
        for debug in (True, False):
            with override_settings(DEBUG=debug):
                for path in ["/api/missing/", "/api/shipments/not-a-uuid/"]:
                    with self.subTest(debug=debug, path=path):
                        response = self.client.get(path)
                        self.assertEqual(response.status_code, 404)
                        self.assert_contract(response, success=False)

    def test_unsupported_method_has_consistent_contract_and_allow_header(self):
        response = self.client.delete("/api/branches/")
        self.assertEqual(response.status_code, 405)
        self.assert_contract(response, success=False)
        self.assertIn("GET", response["Allow"])

    def test_malformed_json_is_enveloped(self):
        response = self.client.post("/api/branches/", "{invalid", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assert_contract(response, success=False)

    def test_unexpected_exception_is_sanitized(self):
        with patch(
            "apps.branches.presentation.views.build_branch_service",
            side_effect=RuntimeError("SECRET_PRIVATE"),
        ):
            with self.assertLogs("config.exceptions", level="ERROR"):
                response = self.client.get("/api/branches/")
        self.assertEqual(response.status_code, 500)
        payload = self.assert_contract(response, success=False)
        self.assertNotIn("SECRET_PRIVATE", str(payload))

    def test_schema_uses_typed_data_inside_envelope_for_every_operation(self):
        schema = self.client.get("/api/schema/").json()
        for path, methods in schema["paths"].items():
            for method, operation in methods.items():
                for code, response in operation["responses"].items():
                    if "content" not in response:
                        continue
                    definition = response["content"]["application/json"]["schema"]
                    if "$ref" in definition:
                        definition = schema["components"]["schemas"][
                            definition["$ref"].rsplit("/", 1)[1]
                        ]
                    self.assertEqual(set(definition["properties"]), FIELDS, (path, method, code))
                    self.assertEqual(set(definition["required"]), FIELDS)
        listing = schema["paths"]["/api/shipments/"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        listing = schema["components"]["schemas"][listing["$ref"].rsplit("/", 1)[1]]
        self.assertEqual(listing["properties"]["data"]["type"], "array")
        self.assertIn("items", listing["properties"]["data"])


class ResponseHelpersTests(SimpleTestCase):
    def test_instances_do_not_share_mutable_messages_or_metadata(self):
        first, second = ApiResponseDto(), ApiResponseDto()
        first.error_messages.append("Error")
        first.meta["page"] = 1
        self.assertEqual(second.error_messages, [])
        self.assertEqual(second.meta, {})

    def test_metadata_can_be_extended_without_overwriting_contract(self):
        response = ApiResponse([1], meta={"page": 2, "total": 5})
        self.assertEqual(response.data["meta"], {"page": 2, "total": 5})
        self.assertTrue(response.data["isSuccess"])

    def test_throttle_retry_header_is_preserved(self):
        response = api_exception_handler(Throttled(wait=7), {})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "7")
        self.assertEqual(response.data["httpCode"], 429)

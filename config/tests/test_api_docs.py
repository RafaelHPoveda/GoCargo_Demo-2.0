from django.test import SimpleTestCase
from django.urls import reverse


class DocumentationTests(SimpleTestCase):
    def test_generated_schema_covers_only_supported_operations(self):
        response = self.client.get(reverse("openapi-schema"))
        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        self.assertEqual(set(paths["/api/branches/"]), {"get", "post"})
        self.assertEqual(set(paths["/api/branches/{branch_id}/"]), {"put", "patch"})
        self.assertEqual(set(paths["/api/shipments/"]), {"get", "post"})
        self.assertEqual(set(paths["/api/shipments/{shipment_id}/"]), {"get"})
        result = paths["/api/shipments/"]["post"]["responses"]
        self.assertIn("201", result)

    def test_scalar_loads_local_generated_schema(self):
        response = self.client.get(reverse("api-docs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("openapi-schema"))
        self.assertContains(response, "proxyUrl: ''")

    def test_documentation_is_read_only(self):
        for name in ("openapi-schema", "api-docs"):
            self.assertEqual(self.client.post(reverse(name)).status_code, 405)

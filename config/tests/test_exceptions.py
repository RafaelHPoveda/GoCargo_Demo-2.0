from django.db import DatabaseError
from django.test import SimpleTestCase

from apps.branches.application.exceptions import BranchNotFoundError as LocalBranchNotFound
from apps.shipments.application.exceptions import BranchNotFoundError
from config.exceptions import api_exception_handler


class ExceptionTranslationTests(SimpleTestCase):
    def test_both_branch_not_found_errors_have_the_same_public_contract(self):
        for error in (LocalBranchNotFound, BranchNotFoundError):
            response = api_exception_handler(error("No existe."), {})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.data["meta"]["errorCode"], "branch_not_found")

    def test_database_errors_outside_repository_do_not_expose_details(self):
        response = api_exception_handler(DatabaseError("private connection details"), {})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", str(response.data))

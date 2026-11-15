import ast
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[2]


class ArchitectureTests(TestCase):
    def test_domain_and_application_do_not_import_frameworks_or_adapters(self):
        for app in ("branches", "shipments"):
            files = list((ROOT / "apps" / app / "domain").rglob("*.py"))
            files += list((ROOT / "apps" / app / "application").rglob("*.py"))
            for path in files:
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                    modules = []
                    if isinstance(node, ast.Import):
                        modules = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        modules = [node.module]
                    for module in modules:
                        with self.subTest(path=path, module=module):
                            self.assertFalse(
                                module.startswith(
                                    (
                                        "django",
                                        "rest_framework",
                                        "requests",
                                        "config",
                                        "drf_spectacular",
                                    )
                                )
                            )
                            self.assertNotIn(".infrastructure", module)
                            self.assertNotIn(".presentation", module)

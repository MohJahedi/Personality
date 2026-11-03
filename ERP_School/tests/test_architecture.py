"""Enforce the dependency seams that make the modular code maintainable."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ArchitectureTests(unittest.TestCase):
    def test_domain_accounting_has_no_school_or_transport_dependency(self):
        tree = ast.parse((ROOT / 'backend/erp_school/modules/accounting/domain.py').read_text())
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertEqual(imports, ['dataclasses'])

    def test_business_modules_do_not_import_http_or_application(self):
        for path in (ROOT / 'backend/erp_school/modules').rglob('*.py'):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse(any(part in ('http', 'application') for part in (node.module or '').split('.')), path)

    def test_frontend_transport_is_centralized(self):
        for path in (ROOT / 'frontend').rglob('*'):
            if path.suffix in ('.ts', '.tsx') and path.name != 'api.ts':
                self.assertNotIn('fetch(', path.read_text(), path)

    def test_font_assets_match_the_pinned_upstream_manifest(self):
        directory = ROOT / 'public/fonts'
        manifest = json.loads((directory / 'SOURCES.json').read_text())
        self.assertEqual(len(manifest), 15)
        for record in manifest:
            data = (directory / record['name']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), record['sha256'])
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(), record['sha'])


if __name__ == '__main__':
    unittest.main()

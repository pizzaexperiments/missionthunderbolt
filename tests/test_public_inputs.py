import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('guard', Path(__file__).resolve().parents[1] / 'scripts/check_public_inputs.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class PublicInputTests(unittest.TestCase):
    def test_private_and_resource_paths(self):
        paths = ['local-original/game.zip', 'local-generated/CODE/1.dat', 'dist/demo.apk',
                 'assets/game.SIT', 'assets/._Game', '__MACOSX/Game', 'assets/fork.rsrc']
        self.assertEqual(guard.violations(paths), sorted(paths))

    def test_source_and_synthetic_fixture_builders(self):
        self.assertEqual(guard.violations(['tests/test_resources.py', 'scripts/import_original.py',
                                          'docs/verification/synthetic-demo.png']), [])

import contextlib
import hashlib
import importlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from test_audit_resources import sample
import import_original

class ImportTests(unittest.TestCase):
    def test_copy_hash_no_overwrite_and_existing_input(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'input.zip';checkout=root/'checkout';checkout.mkdir()
            with zipfile.ZipFile(source,'w') as z:z.writestr('synthetic.txt','synthetic test only')
            with patch.object(import_original,'ROOT',checkout),patch.object(sys,'argv',['import_original.py',str(source)]):
                output=io.StringIO()
                with contextlib.redirect_stdout(output):import_original.main()
                dest=checkout/'local-original/input.zip'
                self.assertEqual(dest.read_bytes(),source.read_bytes())
                self.assertIn(hashlib.sha256(source.read_bytes()).hexdigest(),output.getvalue())
                with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):import_original.main()
            with patch.object(import_original,'ROOT',checkout),patch.object(sys,'argv',['import_original.py',str(dest)]),contextlib.redirect_stdout(io.StringIO()):
                import_original.main()
    def test_invalid_extension_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'input.txt';source.write_text('synthetic')
            with patch.object(import_original,'ROOT',root),patch.object(sys,'argv',['import_original.py',str(source)]),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                import_original.main()
            self.assertFalse((root/'local-original').exists())

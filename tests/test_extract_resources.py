import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
from test_audit_resources import sample
from extract_resources import apple_resource_fork, extract


def double(fork):
    return struct.pack('>II16sHIII', 0x00051607, 0x00020000, bytes(16), 1, 2, 38, len(fork)) + fork

class ExtractTests(unittest.TestCase):
    def test_double_and_zip_determinism(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root / 'synthetic.zip'
            with zipfile.ZipFile(source, 'w') as z:
                z.writestr('__MACOSX/._Game', double(sample(b'CODE', b'synthetic-only', -1)))
            one = extract(source, root / 'one'); two = extract(source, root / 'two')
            self.assertEqual(one, two)
            self.assertEqual((root/'one/manifest.json').read_bytes(), (root/'two/manifest.json').read_bytes())
            self.assertEqual(one[0]['fork'], '__MACOSX/._Game')
            self.assertEqual((root/'one'/one[0]['output']).read_bytes(), b'synthetic-only')
            with self.assertRaises(ValueError): extract(source, root / 'one')

    def test_malformed_double(self):
        b = double(sample())
        for bad in (b[:25], b[:-1], b'X' + b[1:]):
            with self.assertRaises(ValueError): apple_resource_fork(bad)

    def test_unsafe_zip(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=root/'unsafe.zip'
            with zipfile.ZipFile(source,'w') as z: z.writestr('../evil.rsrc',sample())
            with self.assertRaises(ValueError): extract(source,root/'out')
            self.assertFalse((root/'out').exists())

    def test_failure_leaves_no_partial_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=root/'bad.rsrc'; source.write_bytes(sample()[:-1])
            with self.assertRaises(ValueError): extract(source,root/'out')
            self.assertFalse((root/'out').exists())

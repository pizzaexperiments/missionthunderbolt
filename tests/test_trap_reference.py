import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_audit_resources import sample
from prepare_trap_reference import parse_constants,prepare

FIXTURE=b'''enum {
    _SyntheticOne = 0xA123,
    _SyntheticAlias = 0xa123,
    _SyntheticTwo = 0xA456,
    _NotATrap = 0x1234,
};
'''

class TrapReferenceTests(unittest.TestCase):
    def test_exact_constants_and_aliases(self):
        rows=parse_constants(FIXTURE)
        self.assertEqual([r['word'] for r in rows],[0xa123,0xa456])
        self.assertEqual(rows[0]['names'],['_SyntheticAlias','_SyntheticOne'])
        with self.assertRaises(ValueError):parse_constants(b'not a header')
    def test_cli_hash_provenance_and_no_overwrite(self):
        script=Path(__file__).resolve().parents[1]/'scripts/prepare_trap_reference.py'
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'fixture.h';source.write_bytes(FIXTURE)
            command=[sys.executable,str(script),str(source),'--output',str(root/'reference'),'--reference-url','https://example.invalid/synthetic']
            subprocess.run(command,check=True,capture_output=True)
            doc=json.loads((root/'reference/trap-reference.json').read_text())
            self.assertEqual(doc['source_sha256'],hashlib.sha256(FIXTURE).hexdigest())
            self.assertEqual(doc['reference_url'],'https://example.invalid/synthetic')
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
    def test_public_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'fixture.h';source.write_bytes(FIXTURE)
            with self.assertRaises(ValueError):prepare(source,Path(__file__).resolve().parents[1]/'docs')

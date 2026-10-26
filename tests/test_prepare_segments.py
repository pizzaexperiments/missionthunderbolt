import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from test_audit_resources import sample
from extract_resources import extract

class SegmentPreparationTests(unittest.TestCase):
    def test_hash_linked_segment_names_and_unknown_addresses(self):
        script=Path(__file__).resolve().parents[1]/'scripts/prepare_ghidra_segments.py'
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'synthetic.zip'
            with zipfile.ZipFile(source,'w') as z:
                z.writestr('one.rsrc',sample(b'CODE',b'synthetic code placeholder',1))
                z.writestr('two.rsrc',sample(b'CREL',b'synthetic relocation placeholder',1))
            extract(source,root/'extracted')
            subprocess.run([sys.executable,str(script),str(root/'extracted/manifest.json'),'--output',str(root/'segments')],check=True,capture_output=True)
            rows=json.loads((root/'segments/segments.json').read_text())['segments']
            self.assertEqual([r['type'] for r in rows],['CODE','CREL'])
            for row in rows:
                self.assertIsNone(row['runtime_load_address']);self.assertEqual(row['import_base'],0)
                self.assertEqual((root/'segments'/row['output']).stat().st_size,row['bytes'])

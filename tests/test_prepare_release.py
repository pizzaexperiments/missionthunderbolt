import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from test_audit_resources import sample
from prepare_release import prepare

class ReleaseTests(unittest.TestCase):
    def repo(self,root):
        repo=root/'repo';repo.mkdir()
        subprocess.run(['git','init','-q',str(repo)],check=True)
        license_source=Path(__file__).resolve().parents[1]/'LICENSE'
        (repo/'LICENSE').write_bytes(license_source.read_bytes())
        subprocess.run(['git','-C',str(repo),'add','LICENSE'],check=True)
        subprocess.run(['git','-C',str(repo),'-c','user.name=Synthetic Test','-c','user.email=synthetic@example.invalid','commit','-qm','fixture'],check=True)
        return repo
    def test_metadata_hash_and_no_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);repo=self.repo(root);artifact=root/'demo.zip'
            with zipfile.ZipFile(artifact,'w') as z:z.writestr('README.txt','synthetic fixture, not an executable')
            result=prepare(repo,[artifact],root/'review','fixture-1')
            self.assertFalse(result['published']);self.assertEqual(result['artifacts'][0]['sha256'],hashlib.sha256(artifact.read_bytes()).hexdigest())
            sbom=json.loads((root/'review/sbom.spdx.json').read_text());self.assertEqual(sbom['spdxVersion'],'SPDX-2.3')
            with self.assertRaises(ValueError):prepare(repo,[artifact],root/'review','fixture-1')
    def test_private_member_and_dirty_source_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);repo=self.repo(root);artifact=root/'bad.zip'
            with zipfile.ZipFile(artifact,'w') as z:z.writestr('local-original/source.sit','synthetic marker only')
            with self.assertRaises(ValueError):prepare(repo,[artifact],root/'review','fixture-1')
            self.assertFalse((root/'review').exists())
            (repo/'LICENSE').write_text('MIT License\ndirty')
            with self.assertRaises(ValueError):prepare(repo,[artifact],root/'review','fixture-1')

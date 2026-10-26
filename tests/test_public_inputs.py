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

    def test_git_index_guard_rejects_forced_resource_input(self):
        import subprocess,sys,tempfile
        script=Path(__file__).resolve().parents[1]/'scripts/check_public_inputs.py'
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);subprocess.run(['git','init','-q',str(root)],check=True)
            (root/'synthetic.rsrc').write_bytes(b'synthetic fixture only')
            subprocess.run(['git','-C',str(root),'add','synthetic.rsrc'],check=True)
            result=subprocess.run([sys.executable,str(script),'--staged'],cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,1);self.assertIn('synthetic.rsrc',result.stderr)
            subprocess.run(['git','-C',str(root),'rm','--cached','synthetic.rsrc'],check=True,capture_output=True)
            result=subprocess.run([sys.executable,str(script)],cwd=root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0)

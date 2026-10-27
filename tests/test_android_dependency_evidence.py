import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from android_dependency_evidence import collect, elf_info
from prepare_release import dependency_packages, prepare
import test_prepare_release


class DependencyEvidenceTests(unittest.TestCase):
    def fixture(self, root):
        ndk = root/'ndk'; host = ndk/'toolchains/llvm/prebuilt/test-host'
        host.mkdir(parents=True)
        (ndk/'source.properties').write_text('Pkg.Revision = 99.1\n')
        (host/'AndroidVersion.txt').write_text('99.0.1\n')
        for name in ('NOTICE', 'NOTICE.toolchain'):
            (ndk/name).write_text('authored test notice')
        archive = host/'libsynthetic.a'; archive.write_bytes(b'synthetic archive')
        directory = root/'arm64-v8a'; directory.mkdir()
        (directory/'thunderbolt-link.map').write_text(f'0 0 4 4 {archive}(example.o):(.text)\n')
        native = directory/'libthunderbolt.so'; native.write_bytes(b'authored ELF stand-in')
        (directory/'android_gradle_build.json').write_text(json.dumps({'libraries': {'test': {
            'artifactName': 'thunderbolt', 'output': str(native)}}}))
        artifact = root/'test.apk'
        with zipfile.ZipFile(artifact, 'w') as z:
            z.writestr('lib/arm64-v8a/libthunderbolt.so', native.read_bytes())
        runtime = root/'runtime.json'
        runtime.write_text(json.dumps({'schema': 1, 'configuration': 'releaseRuntimeClasspath',
                                       'modules': [], 'artifacts': []}))
        return artifact, ndk, directory, runtime

    def test_hash_binding_and_spdx_static_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); artifact, ndk, directory, runtime = self.fixture(root)
            with patch('android_dependency_evidence.elf_info', return_value=('abc123', ['libc.so'])):
                evidence = collect([artifact], ndk, [directory], runtime, root/'evidence.json')
            packages, ids = dependency_packages(evidence, evidence['artifacts'])
            self.assertEqual(len(ids), 1)
            self.assertEqual(packages[0]['licenseDeclared'], 'NOASSERTION')
            self.assertEqual(packages[0]['checksums'][0]['checksumValue'], evidence['builds']['arm64-v8a']['archives'][0]['sha256'])
            repo = test_prepare_release.ReleaseTests().repo(root)
            result = prepare(repo, [artifact], root/'review', 'fixture-1', dependency_evidence=root/'evidence.json')
            self.assertEqual(result['dependency_evidence'], 'android-dependencies.json')
            spdx = json.loads((root/'review/sbom.spdx.json').read_text())
            self.assertTrue(any(r['relationshipType'] == 'STATIC_LINK' for r in spdx['relationships']))
            with self.assertRaisesRegex(ValueError, 'hashes do not match'):
                dependency_packages(evidence, [{'name': artifact.name, 'sha256': '0'*64}])

    def test_stale_build_id_is_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); artifact, ndk, directory, runtime = self.fixture(root)
            with patch('android_dependency_evidence.elf_info', side_effect=[('aaa', []), ('bbb', [])]):
                with self.assertRaisesRegex(ValueError, 'does not match'):
                    collect([artifact], ndk, [directory], runtime, root/'evidence.json')
            self.assertFalse((root/'evidence.json').exists())

    def test_new_file_dependency_and_foreign_archive_require_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); artifact, ndk, directory, runtime = self.fixture(root)
            original = runtime.read_text(); data = json.loads(original)
            data['artifacts'] = ['local.jar']; runtime.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'Java runtime dependencies'):
                collect([artifact], ndk, [directory], runtime, root/'evidence.json')
            runtime.write_text(original)
            foreign = root/'foreign.a'; foreign.write_bytes(b'synthetic')
            (directory/'thunderbolt-link.map').write_text(f'{foreign}(test.o):(.text)')
            with self.assertRaisesRegex(ValueError, 'non-NDK'):
                collect([artifact], ndk, [directory], runtime, root/'evidence.json')

    def test_elf_needed_and_build_id_parser(self):
        output = 'Build ID: 123abc\n 0x (NEEDED) Shared library: [libc.so]\n'
        with patch('android_dependency_evidence.subprocess.check_output', return_value=output):
            self.assertEqual(elf_info(Path('synthetic-readelf'), Path('synthetic.so')), ('123abc', ['libc.so']))
        with patch('android_dependency_evidence.subprocess.check_output', return_value='no build id'):
            with self.assertRaises(ValueError): elf_info(Path('test'), Path('test'))

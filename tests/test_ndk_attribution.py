"""Authored archive/notice stand-ins; no SDK or historical game inputs required."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from prepare_release import dependency_packages, prepare, reviewed_attribution
import test_prepare_release


class AttributionTests(unittest.TestCase):
    def fixture(self, root):
        ndk = root/'ndk'; ndk.mkdir()
        for name in ('NOTICE', 'NOTICE.toolchain'):
            (ndk/name).write_text('Authored upstream notice stand-in: '+name+'\n')
        archive = ndk/'lib/libsynthetic.a'; archive.parent.mkdir()
        archive.write_bytes(b'authored archive stand-in')
        notices = [{'name': name, 'sha256': hashlib.sha256((ndk/name).read_bytes()).hexdigest()}
                   for name in ('NOTICE', 'NOTICE.toolchain')]
        entry = {'path': 'lib/libsynthetic.a', 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
        evidence = {'schema': 1, 'kind': 'android-ndk-link-review', 'ndk_version': '99.1',
                    'llvm_version': '99.0', 'notices': notices, 'java_runtime_modules': [],
                    'builds': {'test-abi': {'archives': [entry]}}}
        manifest = {'schema': 1, 'kind': 'android-ndk-notice-attribution',
                    'ndk_version': '99.1', 'llvm_version': '99.0', 'notices': notices,
                    'components': {'synthetic': {'licenseDeclared': 'NOASSERTION',
                                                'notice_evidence': 'Authored notice evidence; applicability unresolved.'}},
                    'archives': [dict(abi='test-abi', component='synthetic', **entry)]}
        path = root/'attribution.json'; path.write_text(json.dumps(manifest))
        return ndk, evidence, manifest, path

    def test_preparation_preserves_exact_notices_and_component_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            artifact = root/'demo.zip'
            with zipfile.ZipFile(artifact, 'w') as archive:
                archive.writestr('README.txt', 'synthetic artifact')
            evidence['artifacts'] = [{'name': artifact.name, 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}]
            evidence_path = root/'evidence.json'; evidence_path.write_text(json.dumps(evidence))
            repo = test_prepare_release.ReleaseTests().repo(root)
            result = prepare(repo, [artifact], root/'review', 'fixture-1',
                             dependency_evidence=evidence_path, attribution_manifest=path, ndk=ndk)
            self.assertFalse(result['published'])
            self.assertEqual(result['component_attribution'], 'android-ndk-attribution.json')
            self.assertIn('unresolved', result['attribution_status'])
            self.assertEqual(json.loads((root/'review/android-ndk-attribution.json').read_text()), manifest)
            for notice in ('NOTICE', 'NOTICE.toolchain'):
                self.assertEqual((root/'review/licenses'/notice).read_bytes(), (ndk/notice).read_bytes())
            spdx = json.loads((root/'review/sbom.spdx.json').read_text())
            package = next(p for p in spdx['packages'] if p['SPDXID'].startswith('SPDXRef-NDK-'))
            self.assertIn('Component: synthetic.', package['comment'])
            self.assertIn('Authored notice evidence', package['comment'])
            self.assertEqual(package['licenseDeclared'], 'NOASSERTION')
            self.assertEqual(package['licenseConcluded'], 'NOASSERTION')

    def test_unknown_or_changed_measured_archive_requires_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            for field, value in [('path', 'lib/new.a'), ('sha256', '0'*64)]:
                changed = copy.deepcopy(evidence)
                changed['builds']['test-abi']['archives'][0][field] = value
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'requires attribution review'):
                    reviewed_attribution(path, ndk, changed)

    def test_changed_installed_archive_or_notice_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            for relative in ('lib/libsynthetic.a', 'NOTICE', 'NOTICE.toolchain'):
                target = ndk/relative; original = target.read_bytes(); target.write_bytes(b'changed bytes')
                with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, 'hash does not match attribution'):
                    reviewed_attribution(path, ndk, evidence)
                target.write_bytes(original)

    def test_stale_versions_or_notice_evidence_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            for field in ('ndk_version', 'llvm_version', 'notices'):
                changed = copy.deepcopy(evidence); changed[field] = [] if field == 'notices' else 'other-version'
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'does not match|do not match'):
                    reviewed_attribution(path, ndk, changed)

    def test_unsubstantiated_license_claim_and_missing_evidence_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            for field, value in [('licenseDeclared', 'MIT'), ('notice_evidence', '')]:
                changed = copy.deepcopy(manifest); changed['components']['synthetic'][field] = value
                path.write_text(json.dumps(changed))
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'unresolved archive licenses'):
                    reviewed_attribution(path, ndk, evidence)

    def test_duplicate_unsafe_and_unknown_component_entries_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            changes = []
            duplicate = copy.deepcopy(manifest); duplicate['archives'] *= 2; changes.append(duplicate)
            for field, value in [('path', '../outside.a'), ('component', 'unreviewed')]:
                changed = copy.deepcopy(manifest); changed['archives'][0][field] = value; changes.append(changed)
            for changed in changes:
                path.write_text(json.dumps(changed))
                with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'invalid or duplicate'):
                    reviewed_attribution(path, ndk, evidence)

    def test_manifest_can_cover_more_abis_than_current_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            manifest['archives'].append(dict(manifest['archives'][0], abi='other-abi'))
            path.write_text(json.dumps(manifest))
            _, coverage, _ = reviewed_attribution(path, ndk, evidence)
            evidence['artifacts'] = []
            packages, ids = dependency_packages(evidence, [], coverage)
            self.assertEqual(len(packages), 1)
            self.assertEqual(len(ids), 1)

    def test_manifest_requires_dependency_evidence_and_ndk_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'requires dependency evidence'):
                reviewed_attribution(path, ndk, None)
            repo = test_prepare_release.ReleaseTests().repo(root); artifact = root/'demo.txt'; artifact.write_text('synthetic')
            for arguments in ({'attribution_manifest': path}, {'ndk': ndk}):
                with self.subTest(arguments=arguments), self.assertRaisesRegex(ValueError, 'supplied together'):
                    prepare(repo, [artifact], root/'review', 'fixture-1', **arguments)
            self.assertFalse((root/'review').exists())

    def test_rejected_attribution_leaves_no_partial_review_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ndk, evidence, manifest, path = self.fixture(root)
            artifact = root/'demo.txt'; artifact.write_text('authored artifact')
            evidence['artifacts'] = [{'name': artifact.name, 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}]
            evidence_path = root/'evidence.json'; evidence_path.write_text(json.dumps(evidence))
            manifest['archives'][0]['sha256'] = '0'*64; path.write_text(json.dumps(manifest))
            repo = test_prepare_release.ReleaseTests().repo(root)
            with self.assertRaisesRegex(ValueError, 'requires attribution review'):
                prepare(repo, [artifact], root/'review', 'fixture-1',
                        dependency_evidence=evidence_path, attribution_manifest=path, ndk=ndk)
            self.assertFalse((root/'review').exists())
            self.assertEqual(list(root.glob('.release-review-*')), [])

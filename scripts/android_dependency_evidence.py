#!/usr/bin/env python3
"""Record Android packaged ELF dependencies and linked NDK archives for review."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

from prepare_release import check_members, digest

ABIS = {'arm64-v8a', 'armeabi-v7a', 'x86', 'x86_64'}


def elf_info(tool, path):
    result = subprocess.check_output([str(tool), '--notes', '--dynamic', str(path)], text=True)
    ids = re.findall(r'Build ID: ([0-9a-f]+)', result)
    if len(ids) != 1:
        raise ValueError('ELF must have one build ID')
    return ids[0], sorted(set(re.findall(r'\(NEEDED\).*?\[([^\]]+)\]', result)))


def collect(artifacts, ndk, build_dirs, runtime_report, output):
    ndk = ndk.resolve()
    if output.exists():
        raise ValueError('refusing to overwrite dependency evidence')
    runtime = json.loads(runtime_report.read_text())
    if runtime != {'schema': 1, 'configuration': 'releaseRuntimeClasspath', 'modules': [], 'artifacts': []}:
        raise ValueError('Java runtime dependencies require an expanded license/component review')
    properties = dict(re.findall(r'^(Pkg\.[A-Za-z]+)\s*=\s*(.+)$',
                                 (ndk/'source.properties').read_text(), re.M))
    hosts = list((ndk/'toolchains/llvm/prebuilt').glob('*'))
    if len(hosts) != 1:
        raise ValueError('select an NDK with exactly one host toolchain')
    host = hosts[0]
    tool = host/'bin/llvm-readelf'
    if not tool.exists():
        tool = host/'bin/llvm-readelf.exe'
    builds = {}
    for directory in build_dirs:
        abi = directory.name
        if abi not in ABIS or abi in builds:
            raise ValueError('duplicate or unsupported ABI build directory')
        mapping = directory/'thunderbolt-link.map'
        text = mapping.read_text()
        # lld map lists only archives contributing retained sections. Record all
        # listed archive inputs; do not guess which individual functions survive.
        archives = []
        for name in sorted(set(re.findall(r'(\S+\.a)\(', text))):
            archive = Path(name).resolve()
            if not archive.is_relative_to(ndk):
                raise ValueError('non-NDK static dependency requires separate review')
            archives.append({'path': archive.relative_to(ndk).as_posix(), 'sha256': digest(archive)})
        if not archives:
            raise ValueError('missing static runtime archive evidence')
        metadata = json.loads((directory/'android_gradle_build.json').read_text())
        libraries = metadata['libraries']
        native = [Path(v['output']) for v in libraries.values() if v.get('artifactName') == 'thunderbolt']
        if len(native) != 1:
            raise ValueError('expected exactly one native build output')
        build_id, needed = elf_info(tool, native[0])
        builds[abi] = {'build_id': build_id, 'needed': needed, 'archives': archives,
                       'link_map_sha256': digest(mapping)}
    rows = []
    if not builds or not artifacts:
        raise ValueError('artifacts and ABI builds are required')
    with tempfile.TemporaryDirectory() as temp:
        for artifact in artifacts:
            check_members(artifact)
            members = []
            with zipfile.ZipFile(artifact) as package:
                if len(package.namelist()) != len(set(package.namelist())):
                    raise ValueError('duplicate archive members')
                for name in package.namelist():
                    match = re.fullmatch(r'(?:base/)?lib/([^/]+)/([^/]+\.so)', name)
                    if not match:
                        if name.endswith('.so'):
                            raise ValueError('unexpected native library location')
                        continue
                    abi, library = match.groups()
                    prefix = 'base/' if artifact.suffix == '.aab' else ''
                    if name != f'{prefix}lib/{abi}/{library}':
                        raise ValueError('native member does not match package layout')
                    if library != 'libthunderbolt.so' or abi not in builds:
                        raise ValueError('native library lacks dependency evidence')
                    data = package.read(name)
                    path = Path(temp)/'library.so'
                    path.write_bytes(data)
                    build_id, needed = elf_info(tool, path)
                    if build_id != builds[abi]['build_id'] or needed != builds[abi]['needed']:
                        raise ValueError('packaged ELF does not match linked build')
                    members.append({'member': name, 'abi': abi, 'sha256': hashlib.sha256(data).hexdigest()})
                if {m['abi'] for m in members} != set(builds):
                    raise ValueError('artifact ABI set does not match evidence')
            rows.append({'name': artifact.name, 'sha256': digest(artifact), 'native_members': members})
    report = {'schema': 1, 'kind': 'android-ndk-link-review', 'artifacts': rows,
              'ndk_version': properties['Pkg.Revision'],
              'llvm_version': (host/'AndroidVersion.txt').read_text().strip().splitlines()[0],
              'java_runtime_modules': [], 'builds': builds,
              'notices': [{'name': n, 'sha256': digest(ndk/n)} for n in ('NOTICE', 'NOTICE.toolchain')],
              'limitations': ['Link maps/build IDs are correspondence evidence, not signed build attestations',
                              'NDK archives are recorded as a composite runtime; component license review remains required',
                              'Build tools and OS-provided libraries are not bundled runtime dependencies']}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact', type=Path, action='append', required=True)
    p.add_argument('--ndk', type=Path, required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--build-dir', type=Path, action='append')
    group.add_argument('--build-root', type=Path, help='Release .cxx/RelWithDebInfo root; stale duplicate ABI maps are rejected')
    p.add_argument('--runtime-report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        directories = a.build_dir if a.build_dir else sorted(p.parent for p in a.build_root.rglob('thunderbolt-link.map'))
        report = collect(a.artifact, a.ndk, directories, a.runtime_report, a.output)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as e:
        p.error(str(e))
    print(f'Recorded {len(report["builds"])} ABIs; dependency/license review remains required')


if __name__ == '__main__':
    main()

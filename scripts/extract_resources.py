#!/usr/bin/env python3
"""Local-only extraction from raw resource forks, AppleDouble/AppleSingle or ZIP."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import tempfile
import zipfile
from audit_resources import resources

MAX_BYTES = 256 * 1024 * 1024
MAX_MEMBERS = 4096


def apple_resource_fork(data):
    if len(data) < 26:
        raise ValueError('truncated AppleDouble/AppleSingle header')
    magic, version = struct.unpack_from('>II', data)
    if magic not in (0x00051607, 0x00051600) or version != 0x00020000:
        raise ValueError('unsupported AppleDouble/AppleSingle magic or version')
    n = struct.unpack_from('>H', data, 24)[0]
    header_end = 26 + n * 12
    if header_end > len(data):
        raise ValueError('truncated AppleDouble entry table')
    entries, ranges = {}, []
    for i in range(n):
        kind, offset, size = struct.unpack_from('>III', data, 26 + i * 12)
        if kind in entries or offset < header_end or offset + size > len(data):
            raise ValueError('invalid/duplicate AppleDouble entry')
        if size and any(max(offset, start) < min(offset + size, end) for start, end in ranges):
            raise ValueError('overlapping AppleDouble entries')
        ranges.append((offset, offset + size))
        entries[kind] = data[offset:offset + size]
    if 2 not in entries:
        raise ValueError('AppleDouble has no resource fork entry (ID 2)')
    return entries[2]


def source_forks(path):
    if path.is_dir():
        members=sorted(path.rglob('*'))
        if any(p.is_symlink() for p in members):
            raise ValueError('symlinks in resource source tree are not supported')
        files=[p for p in members if p.is_file() and (p.name.startswith('._') or p.suffix.lower()=='.rsrc')]
        if len(files)>MAX_MEMBERS or sum(p.stat().st_size for p in files)>MAX_BYTES:
            raise ValueError('resource source tree exceeds limits')
        for member in files:
            data=member.read_bytes()
            if member.name.startswith('._') or data[:4] in (b'\x00\x05\x16\x07',b'\x00\x05\x16\x00'):
                data=apple_resource_fork(data)
            yield str(member.relative_to(path)),data
        return
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('input exceeds size limit')
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_MEMBERS or sum(i.file_size for i in entries) > MAX_BYTES:
                raise ValueError('ZIP exceeds member/expanded size limit')
            names = set()
            for info in sorted(entries, key=lambda x: x.filename):
                name = PurePosixPath(info.filename)
                if (name.is_absolute() or '..' in name.parts or '\\' in info.filename
                        or info.filename in names or stat.S_ISLNK(info.external_attr >> 16)):
                    raise ValueError('unsafe or duplicate ZIP member')
                names.add(info.filename)
                if info.is_dir():
                    continue
                if name.name.startswith('._'):
                    yield info.filename, apple_resource_fork(archive.read(info))
                elif name.suffix.lower() == '.rsrc':
                    yield info.filename, archive.read(info)
    else:
        data = path.read_bytes()
        if data[:4] in (b'\x00\x05\x16\x07', b'\x00\x05\x16\x00'):
            data = apple_resource_fork(data)
        yield path.name, data


def extract(source, output):
    source, output = source.resolve(), output.resolve()
    repo = Path(__file__).resolve().parents[1]
    if output.is_relative_to(repo) and not output.is_relative_to(repo / 'local-generated'):
        raise ValueError('outputs inside the checkout must be under ignored local-generated/')
    if output.exists():
        raise ValueError('refusing to overwrite an existing output directory')
    records, payloads = [], []
    for index, (fork_name, fork) in enumerate(source_forks(source)):
        for typ, rid, payload in resources(fork):
            relative = f'resources/{index:04d}/{typ.hex()}_{rid}.bin'
            records.append({'source': source.name, 'fork': fork_name, 'type': typ.decode('mac_roman'),
                            'id': rid, 'bytes': len(payload),
                            'sha256': hashlib.sha256(payload).hexdigest(), 'output': relative})
            payloads.append((relative, payload))
    if not records:
        raise ValueError('no resources found; no output written')
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.extract-', dir=output.parent))
    try:
        for relative, payload in payloads:
            target = temp / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        (temp / 'manifest.json').write_text(json.dumps({'schema': 1, 'resources': records},
                                                      indent=2, ensure_ascii=True) + '\n')
        temp.rename(output)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=Path('local-generated/extracted'))
    args = parser.parse_args()
    try:
        records = extract(args.source, args.output)
    except (ValueError, OSError, zipfile.BadZipFile, RuntimeError) as e:
        parser.error(str(e))
    print(f'Extracted {len(records)} resources locally. No original data uploaded.')

if __name__ == '__main__':
    main()

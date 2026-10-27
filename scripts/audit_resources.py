#!/usr/bin/env python3
"""Bounds-checked, metadata-only Macintosh resource-fork auditor."""
import argparse
import csv
import hashlib
from pathlib import Path
import struct


def u16(b, i):
    if i < 0 or i + 2 > len(b):
        raise ValueError('truncated u16')
    return struct.unpack_from('>H', b, i)[0]


def u32(b, i):
    if i < 0 or i + 4 > len(b):
        raise ValueError('truncated u32')
    return struct.unpack_from('>I', b, i)[0]


def resources(b):
    """Yield (four-byte type, signed ID, payload); reject malformed references."""
    if len(b) < 16:
        raise ValueError('truncated resource header')
    data, mapping, data_len, map_len = struct.unpack_from('>IIII', b)
    data_end, map_end = data + data_len, mapping + map_len
    if (data < 16 or mapping < 16 or data_end > len(b) or map_end > len(b)
            or map_len < 28 or max(data, mapping) < min(data_end, map_end)):
        raise ValueError('invalid/overlapping resource sections')
    types = mapping + u16(b, mapping + 24)
    names = mapping + u16(b, mapping + 26)
    if not mapping + 28 <= types <= map_end - 2 or not types + 2 <= names <= map_end:
        raise ValueError('invalid type/name list')
    raw_count = u16(b, types)
    count = 0 if raw_count == 0xffff else raw_count + 1
    type_end = types + 2 + count * 8
    if type_end > names:
        raise ValueError('type entries out of bounds')
    seen = set()
    ref_ranges = []
    records = []
    for i in range(count):
        t = types + 2 + i * 8
        typ = bytes(b[t:t + 4])
        n = u16(b, t + 4) + 1
        refs = types + u16(b, t + 6)
        ref_end = refs + 12 * n
        if refs < type_end or ref_end > names:
            raise ValueError('resource references out of bounds')
        if any(max(refs, x) < min(ref_end, y) for x, y in ref_ranges):
            raise ValueError('overlapping resource references')
        ref_ranges.append((refs, ref_end))
        for j in range(n):
            r = refs + j * 12
            rid = struct.unpack_from('>h', b, r)[0]
            if (typ, rid) in seen:
                raise ValueError('duplicate resource type/ID')
            seen.add((typ, rid))
            name = u16(b, r + 2)
            if name != 0xffff:
                start = names + name
                if start >= map_end or start + 1 + b[start] > map_end:
                    raise ValueError('resource name out of bounds')
            offset = int.from_bytes(b[r + 5:r + 8], 'big')
            a = data + offset
            if a + 4 > data_end:
                raise ValueError('resource offset out of bounds')
            size = u32(b, a)
            if a + 4 + size > data_end:
                raise ValueError('resource payload out of bounds')
            records.append((typ, rid, b[a + 4:a + 4 + size]))
    yield from sorted(records, key=lambda r: (r[0], r[1]))


def parse_fork(b):
    for typ, rid, payload in resources(b):
        w = h = ''
        if typ == b'PICT' and len(payload) >= 10:
            top, left, bottom, right = struct.unpack_from('>hhhh', payload, 2)
            w, h = right - left, bottom - top
        yield (typ.decode('mac_roman'), rid, len(payload), w, h,
               hashlib.sha256(payload).hexdigest())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('resource_dir', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if not a.resource_dir.is_dir():
        p.error('resource_dir missing')
    rows = []
    try:
        for path in sorted(a.resource_dir.rglob('*.rsrc')):
            for record in parse_fork(path.read_bytes()):
                rows.append((str(path.relative_to(a.resource_dir)), *record))
    except ValueError as e:
        p.error(str(e))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['fork', 'type', 'id', 'bytes', 'pict_width', 'pict_height', 'sha256'])
        writer.writerows(rows)
    print('Audited', len(rows), 'resources')

if __name__ == '__main__':
    main()

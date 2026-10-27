#!/usr/bin/env python3
"""Compare local indexed PICT output with ImageMagick; preserve private evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from pict_catalog import decode, manifest_inputs


def compare(data, tool):
    width, height, expected = decode(data)
    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp)/'input.pict'; raw = Path(temp)/'reference.rgb'
        source.write_bytes(bytes(512)+data)
        # Keep 16-bit channels: ImageMagick's normal 8-bit rounding differs
        # from this decoder's explicit high-byte projection of QuickDraw RGB.
        command = [tool, '-limit', 'memory', '128MiB', '-limit', 'map', '256MiB',
                   '-limit', 'disk', '0', '-limit', 'time', '15', 'PICT:'+str(source),
                   '-depth', '16', '-endian', 'MSB', '-write', 'RGB:'+str(raw),
                   '-format', '%w %h', 'info:']
        result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=True)
        dimensions = tuple(int(n) for n in result.stdout.split())
        if dimensions != (width, height):
            return {'status': 'dimension-mismatch', 'width': width, 'height': height,
                    'reference_dimensions': list(dimensions)}
        if raw.stat().st_size != width*height*6:
            raise ValueError('independent decoder returned unexpected RGB16 length')
        reference = raw.read_bytes()[::2]
    differences = [i for i in range(width*height) if expected[i*3:i*3+3] != reference[i*3:i*3+3]]
    return {'status': 'exact' if not differences else 'pixel-mismatch',
            'width': width, 'height': height, 'different_pixels': len(differences),
            'maximum_channel_delta': max(abs(a-b) for a,b in zip(expected, reference)),
            'first_different_pixel': [differences[0] % width, differences[0] // width] if differences else None,
            'rgb_sha256': hashlib.sha256(expected).hexdigest(),
            'reference_rgb_sha256': hashlib.sha256(reference).hexdigest()}


def verify(inputs, output, tool):
    repo = Path(__file__).resolve().parents[1]; output = output.resolve()
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):
        raise ValueError('original comparison evidence must remain under local-generated/ or outside checkout')
    if output.exists():
        raise ValueError('refusing to overwrite comparison report')
    version = subprocess.check_output([tool, '-version'], text=True, timeout=10).splitlines()[0]
    rows = []
    for record, data in inputs:
        row = {key: record[key] for key in ('fork', 'id', 'sha256')}
        try:
            row.update(compare(data, tool))
        except (ValueError, OSError, subprocess.SubprocessError) as e:
            # Avoid embedding commands/temp paths or huge external stderr.
            row.update(status='failed', reason=type(e).__name__)
        rows.append(row)
    if not rows:
        raise ValueError('no PICT inputs')
    counts = {status: sum(r['status'] == status for r in rows)
              for status in ('exact', 'pixel-mismatch', 'dimension-mismatch', 'failed')}
    report = {'schema': 1, 'reference_tool': version,
              'comparison': 'RGB16 big-endian channels projected to their high bytes; no pixel tolerance',
              'limitations': 'Independent decoder agreement is not a Classic Mac runtime screenshot comparison',
              'counts': counts, 'resources': rows}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--manifest', type=Path)
    group.add_argument('--standalone', type=Path, nargs='+')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--imagemagick', default='convert', help='ImageMagick convert or magick executable')
    a = p.parse_args()
    tool = shutil.which(a.imagemagick)
    if not tool:
        p.error('ImageMagick executable is unavailable')
    try:
        if a.manifest:
            inputs = manifest_inputs(a.manifest, 'PICT')
        else:
            inputs = []
            for path in a.standalone:
                data = path.read_bytes()
                if len(data) < 522:
                    raise ValueError('truncated standalone PICT')
                inputs.append(({'fork': path.name, 'id': None, 'sha256': hashlib.sha256(data).hexdigest()}, data[512:]))
        report = verify(inputs, a.output, tool)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as e:
        p.error(str(e))
    print(json.dumps(report['counts']))
    return 0 if report['counts']['exact'] == len(report['resources']) else 2


if __name__ == '__main__':
    raise SystemExit(main())

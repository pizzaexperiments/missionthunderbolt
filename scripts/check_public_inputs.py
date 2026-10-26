#!/usr/bin/env python3
"""Reject historical inputs/build outputs in the Git index; no input bytes read."""
import argparse
from pathlib import PurePosixPath
import subprocess
import sys

PRIVATE_ROOTS = {'local-original', 'local-generated', 'dist'}
RESTRICTED_SUFFIXES = {'.sit', '.sitx', '.hqx', '.rsrc', '.pict', '.snd', '.apk', '.aab'}

def violations(paths):
    rejected = []
    for name in paths:
        p = PurePosixPath(name)
        if (set(p.parts) & PRIVATE_ROOTS or p.suffix.lower() in RESTRICTED_SUFFIXES
                or p.name.startswith('._') or '__MACOSX' in p.parts):
            rejected.append(name)
    return sorted(set(rejected))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Check added/modified index paths only')
    args = parser.parse_args()
    command = (['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z']
               if args.staged else ['git', 'ls-files', '-z'])
    paths = subprocess.check_output(command).decode('utf-8', errors='surrogateescape').split('\0')
    rejected = violations(filter(None, paths))
    if rejected:
        print('Restricted input/output paths in Git index:', file=sys.stderr)
        for path in rejected:
            print('  ' + repr(path), file=sys.stderr)
        print('Keep original inputs and derived research files in ignored local directories.', file=sys.stderr)
        return 1
    print('Public-input path check passed (metadata only; not a copyright determination)')
    return 0

if __name__ == '__main__':
    sys.exit(main())

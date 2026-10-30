#!/usr/bin/env python3
"""Measure the installed synthetic Android demo on one explicitly selected device.

Force-stops its process and sends WAIT keys, changing synthetic turns. Does not
clear user data, drop OS caches, install/build APKs or set pass/fail thresholds.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import re
import shlex
import statistics
import subprocess
import tempfile
import time

PACKAGE = 'org.missionthunderbolt.prototype'
COMPONENT = PACKAGE + '/.MainActivity'


class AdbTransport:
    def __init__(self, serial):
        self.prefix = ['adb', '-s', serial]

    def shell(self, *args):
        return subprocess.check_output([*self.prefix, 'shell', *args], text=True, timeout=180)

    def pull(self, remote, local):
        subprocess.run([*self.prefix, 'pull', remote, str(local)], check=True, capture_output=True, timeout=180)


class DirectEmulatorTransport:
    """Optional local-adbd fallback when a host adb server cannot start."""
    def __init__(self, port):
        from adb_shell.adb_device import AdbDeviceTcp
        self.adb = AdbDeviceTcp('127.0.0.1', port, default_transport_timeout_s=90)
        self.adb.connect(auth_timeout_s=30)

    def shell(self, *args):
        return self.adb.shell(shlex.join(args), transport_timeout_s=90, read_timeout_s=180, timeout_s=180)

    def pull(self, remote, local):
        self.adb.pull(remote, str(local), transport_timeout_s=90)


def summarize(values):
    if not values:
        return None
    ordered = sorted(values)
    return {'count': len(values), 'min': ordered[0], 'median': statistics.median(values),
            'p95_nearest_rank': ordered[math.ceil(.95 * len(values)) - 1], 'max': ordered[-1]}


def parse_launch(text):
    if not re.search(r'^Status:\s*ok\s*$', text, re.M):
        raise ValueError('Activity Manager did not report Status: ok')
    if re.search(r'Warning:|Error:|Exception', text):
        raise ValueError('Activity Manager reported a warning/error instead of a fresh launch')
    result = {}
    for field in ('ThisTime', 'TotalTime', 'WaitTime'):
        found = re.search(r'^' + field + r':\s*(\d+)\s*$', text, re.M)
        if not found:
            raise ValueError('missing launch field ' + field)
        result[field + '_ms'] = int(found.group(1))
    if not re.search(r'^Activity:\s*' + re.escape(COMPONENT) + r'\s*$', text, re.M):
        raise ValueError('unexpected launched Activity')
    return result


def parse_pss(text):
    # API 23 table TOTAL's first column is Pss Total; newer summaries label it.
    summary = re.search(r'^\s*TOTAL PSS:\s*(\d+)\b', text, re.M)
    table = re.search(r'^\s*TOTAL\s+(\d+)\b', text, re.M)
    found = summary or table
    if not found:
        raise ValueError('missing TOTAL PSS in dumpsys meminfo')
    return int(found.group(1))


def parse_frames(text):
    durations = []
    excluded = 0
    for block in text.split('---PROFILEDATA---')[1::2]:
        rows = list(csv.reader(io.StringIO(block.strip())))
        if not rows:
            continue
        header = [column.strip() for column in rows[0]]
        required = ('Flags', 'IntendedVsync', 'FrameCompleted')
        if not all(column in header for column in required):
            raise ValueError('unknown gfxinfo frame columns')
        positions = [header.index(column) for column in required]
        for row in rows[1:]:
            if not row:
                continue
            if len(row) <= max(positions):
                raise ValueError('truncated gfxinfo frame row')
            flags, start, end = (int(row[index].strip()) for index in positions)
            if flags != 0 or start <= 0 or end < start or end == 9223372036854775807:
                excluded += 1
            else:
                durations.append((end - start) / 1_000_000)
    total = re.search(r'Total frames rendered:\s*(\d+)', text)
    jank = re.search(r'Janky frames:\s*(\d+)\s*\(([\d.]+)%\)', text)
    return {'frame_duration_ms': summarize(durations), 'excluded_frame_rows': excluded,
            'framework_total_frames': int(total.group(1)) if total else None,
            'framework_janky_frames': int(jank.group(1)) if jank else None,
            'framework_janky_percent': float(jank.group(2)) if jank else None,
            'status': 'measured' if durations else 'no_valid_frame_rows'}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def package_metadata(text):
    result = {}
    for field in ('versionName', 'versionCode', 'targetSdk', 'minSdk'):
        match = re.search(r'\b' + field + r'=([^\s]+)', text)
        result[field] = match.group(1) if match else None
    result['debuggable'] = bool(re.search(r'\bDEBUGGABLE\b', text))
    if not result['targetSdk']:
        raise ValueError('installed package lacks targetSdk metadata')
    return result


def run(transport, apk, output, launches=5, actions=24, interval=.1, selection=None):
    output.mkdir(parents=True, exist_ok=True)
    if not 1 <= launches <= 30 or not 1 <= actions <= 120 or not 0 <= interval <= 5:
        raise ValueError('launch/action counts or interval outside supported bounds')
    local_hash = sha256(apk)
    paths = transport.shell('pm', 'path', PACKAGE).splitlines()
    if len(paths) != 1 or not paths[0].startswith('package:/'):
        raise ValueError('expected exactly one installed synthetic demo APK')
    installed_path = paths[0].removeprefix('package:').strip()
    with tempfile.TemporaryDirectory() as directory:
        installed = Path(directory) / 'installed.apk'
        transport.pull(installed_path, installed)
        installed_hash = sha256(installed)
    if installed_hash != local_hash:
        raise ValueError('installed APK does not match the supplied APK SHA-256')
    package_raw = transport.shell('dumpsys', 'package', PACKAGE)
    properties = {name: transport.shell('getprop', name).strip() for name in (
        'ro.build.version.sdk', 'ro.build.version.release', 'ro.product.cpu.abi',
        'ro.product.cpu.abilist', 'ro.product.manufacturer', 'ro.product.model',
        'ro.build.fingerprint', 'ro.kernel.qemu')}
    report = {'schema': 1, 'measured_at_utc': datetime.now(timezone.utc).isoformat(),
              'selection': selection, 'package': PACKAGE, 'installed': package_metadata(package_raw),
              'apk': {'sha256': local_hash, 'bytes': apk.stat().st_size, 'installed_matches': True},
              'device': properties, 'host': {'system': platform.system(), 'machine': platform.machine()},
              'font_scale_setting': transport.shell('settings', 'get', 'system', 'font_scale').strip(),
              'display': transport.shell('wm', 'size').strip(),
              'method': 'process-cold force-stop; OS caches retained; scripted WAIT keys; no performance threshold',
              'launches': []}
    for index in range(launches):
        transport.shell('am', 'force-stop', PACKAGE)
        processes = transport.shell('ps')
        if any(line.split()[-1] == PACKAGE for line in processes.splitlines() if line.split()):
            raise RuntimeError('synthetic process remained after force-stop')
        start = time.monotonic()
        raw = transport.shell('am', 'start', '-W', '-n', COMPONENT)
        elapsed_ms = (time.monotonic() - start) * 1000
        (output / f'launch-{index + 1}.txt').write_text(raw)
        report['launches'].append({**parse_launch(raw), 'host_round_trip_ms': elapsed_ms})
    report['launch_summary_ms'] = {
        field: summarize([sample[field] for sample in report['launches']])
        for field in ('ThisTime_ms', 'TotalTime_ms', 'WaitTime_ms', 'host_round_trip_ms')}
    before = transport.shell('dumpsys', 'meminfo', PACKAGE)
    transport.shell('dumpsys', 'gfxinfo', PACKAGE, 'reset')
    for _ in range(actions):
        transport.shell('input', 'keyevent', '62')  # Space: synthetic WAIT, stable at every map position.
        time.sleep(interval)
    time.sleep(1)  # Allow the final invalidated view to reach a frame completion.
    frames = transport.shell('dumpsys', 'gfxinfo', PACKAGE, 'framestats')
    after = transport.shell('dumpsys', 'meminfo', PACKAGE)
    (output / 'gfxinfo.txt').write_text(frames)
    (output / 'meminfo-before.txt').write_text(before)
    (output / 'meminfo-after.txt').write_text(after)
    report['actions'] = {'keycode': 62, 'count': actions, 'interval_seconds': interval,
                         'delivery': 'input keyevent; gameplay turn count not asserted'}
    report['rendering'] = parse_frames(frames)
    report['pss_kib'] = {'before_actions': parse_pss(before), 'after_actions': parse_pss(after)}
    report['limits'] = ['Process-cold, not cache-cold; no first-launch/install timing.',
                        'Synthetic installed artifact; no build performed by this tool.',
                        'Frame timing measures Android view pipeline, not original gameplay or sustained FPS.',
                        'PSS is two snapshots, not peak memory or a leak test.',
                        'Host/transport overhead, OS caches and concurrent load affect measurements.',
                        'No physical ARM64, API35 runtime, battery or thermal qualification implied.']
    (output / 'android-performance.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--serial', help='Explicit adb device serial; never auto-selects')
    selection.add_argument('--direct-emulator', type=int, metavar='LOCAL_ADBD_PORT')
    parser.add_argument('--apk', type=Path, required=True, help='Existing APK; installed bytes must match')
    parser.add_argument('--output', type=Path, default=Path('dist/verification/android-performance'))
    parser.add_argument('--launches', type=int, default=5)
    parser.add_argument('--actions', type=int, default=24)
    parser.add_argument('--interval', type=float, default=.1)
    args = parser.parse_args()
    transport = AdbTransport(args.serial) if args.serial else DirectEmulatorTransport(args.direct_emulator)
    report = run(transport, args.apk, args.output, args.launches, args.actions, args.interval,
                 args.serial or f'local-adbd:{args.direct_emulator}')
    print(json.dumps({'launch_summary_ms': report['launch_summary_ms'], 'rendering': report['rendering'],
                      'pss_kib': report['pss_kib'], 'apk': report['apk']}, indent=2))


if __name__ == '__main__':
    main()

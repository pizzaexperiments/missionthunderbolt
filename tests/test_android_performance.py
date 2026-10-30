import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('android_performance', Path(__file__).parents[1] / 'scripts/android_performance.py')
performance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(performance)


class AndroidPerformanceTests(unittest.TestCase):
    def test_launch_requires_fresh_expected_activity_and_complete_timings(self):
        text = 'Status: ok\nActivity: ' + performance.COMPONENT + '\nThisTime: 12\nTotalTime: 13\nWaitTime: 14\n'
        self.assertEqual(performance.parse_launch(text)['TotalTime_ms'], 13)
        for invalid in (text.replace('Status: ok', 'Status: timeout'), text.replace('WaitTime: 14', ''),
                        text.replace(performance.COMPONENT, 'other/.Activity'), text + 'Warning: reused Activity\n'):
            with self.assertRaises(ValueError):
                performance.parse_launch(invalid)

    def test_pss_reads_total_column_or_explicit_summary(self):
        self.assertEqual(performance.parse_pss('   TOTAL 12345 6000 8000 0\n'), 12345)
        self.assertEqual(performance.parse_pss(' TOTAL 12345 1\n TOTAL PSS: 23456 TOTAL RSS: 99999\n'), 23456)
        with self.assertRaises(ValueError):
            performance.parse_pss('Native Heap 100\n')

    def test_frame_columns_order_multiple_windows_and_invalid_flags(self):
        block = '\n---PROFILEDATA---\nFrameCompleted,Flags,IntendedVsync,\n21000000,0,1000000,\n'
        text = 'Total frames rendered: 3\nJanky frames: 1 (33.33%)\n' + block
        text += '22000000,1,2000000,\n---PROFILEDATA---\nWindow two' + block + '---PROFILEDATA---\n'
        result = performance.parse_frames(text)
        self.assertEqual(result['frame_duration_ms']['count'], 2)
        self.assertEqual(result['frame_duration_ms']['median'], 20)
        self.assertEqual(result['excluded_frame_rows'], 1)
        self.assertEqual(result['framework_janky_percent'], 33.33)

    def test_empty_frames_are_unmeasured_and_malformed_frames_rejected(self):
        self.assertEqual(performance.parse_frames('No frames')['status'], 'no_valid_frame_rows')
        for text in ('---PROFILEDATA---\nUnknown,Columns\n---PROFILEDATA---',
                     '---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted\n0,10\n---PROFILEDATA---'):
            with self.assertRaises(ValueError):
                performance.parse_frames(text)

    def test_frame_clock_sentinels_and_negative_durations_are_excluded(self):
        text = '---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted\n0,0,20\n0,30,20\n0,1,9223372036854775807\n---PROFILEDATA---'
        result = performance.parse_frames(text)
        self.assertEqual(result['excluded_frame_rows'], 3)
        self.assertIsNone(result['frame_duration_ms'])

    def test_summary_nearest_rank_and_package_identity(self):
        self.assertEqual(performance.summarize([4, 1, 2, 3]), {'count': 4, 'min': 1, 'median': 2.5, 'p95_nearest_rank': 4, 'max': 4})
        self.assertIsNone(performance.summarize([]))
        metadata = performance.package_metadata('versionCode=1 minSdk=23 targetSdk=35\nversionName=0.1\nflags=[ DEBUGGABLE HAS_CODE ]')
        self.assertTrue(metadata['debuggable'])
        self.assertEqual(metadata['targetSdk'], '35')
        with self.assertRaises(ValueError):
            performance.package_metadata('not installed')


class AuthoredDevice:
    def __init__(self, installed, surviving=False):
        self.installed = installed
        self.surviving = surviving
        self.commands = []

    def pull(self, remote, local):
        shutil.copyfile(self.installed, local)

    def shell(self, *args):
        self.commands.append(args)
        if args[:2] == ('pm', 'path'):
            return 'package:/data/app/synthetic/base.apk\n'
        if args[:2] == ('dumpsys', 'package'):
            return 'targetSdk=35 versionName=authored versionCode=1\nflags=[ DEBUGGABLE ]'
        if args == ('ps',):
            return 'USER PID NAME\n' + ('app 123 ' + performance.PACKAGE if self.surviving else '')
        if args[:2] == ('am', 'start'):
            return 'Status: ok\nActivity: ' + performance.COMPONENT + '\nThisTime: 10\nTotalTime: 11\nWaitTime: 12\n'
        if args[:2] == ('dumpsys', 'meminfo'):
            return '  TOTAL 1024 512 100\n'
        if args[:2] == ('dumpsys', 'gfxinfo') and args[-1] == 'framestats':
            return '---PROFILEDATA---\nFlags,IntendedVsync,FrameCompleted\n0,1000000,2000000\n---PROFILEDATA---\n'
        return ''


class AndroidPerformanceCollectionTests(unittest.TestCase):
    def test_authored_collection_requires_identity_and_preserves_raw_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk = root / 'authored.apk'
            apk.write_bytes(b'authored test bytes, not an Android APK')
            device = AuthoredDevice(apk)
            with patch.object(performance.time, 'sleep'):
                result = performance.run(device, apk, root / 'report', launches=2, actions=3)
            self.assertEqual(result['launch_summary_ms']['TotalTime_ms']['median'], 11)
            self.assertEqual(result['rendering']['frame_duration_ms']['median'], 1)
            self.assertEqual(result['pss_kib']['after_actions'], 1024)
            self.assertTrue(result['apk']['installed_matches'])
            self.assertEqual(device.commands.count(('input', 'keyevent', '62')), 3)
            self.assertEqual(device.commands.count(('am', 'force-stop', performance.PACKAGE)), 2)
            self.assertTrue((root / 'report' / 'launch-2.txt').is_file())
            self.assertTrue((root / 'report' / 'gfxinfo.txt').is_file())
            self.assertTrue((root / 'report' / 'android-performance.json').is_file())

    def test_mismatched_artifact_rejects_before_force_stop_or_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk = root / 'expected.apk'; apk.write_bytes(b'expected')
            installed = root / 'installed.apk'; installed.write_bytes(b'other artifact')
            device = AuthoredDevice(installed)
            with self.assertRaisesRegex(ValueError, 'does not match'):
                performance.run(device, apk, root / 'report')
            self.assertFalse(any(command[0] in ('am', 'input') for command in device.commands))

    def test_surviving_process_rejects_before_reporting_cold_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk = root / 'authored.apk'; apk.write_bytes(b'authored')
            device = AuthoredDevice(apk, surviving=True)
            with self.assertRaisesRegex(RuntimeError, 'remained after force-stop'):
                performance.run(device, apk, root / 'report')
            self.assertFalse(any(command[:2] == ('am', 'start') for command in device.commands))
            self.assertFalse((root / 'report' / 'android-performance.json').exists())

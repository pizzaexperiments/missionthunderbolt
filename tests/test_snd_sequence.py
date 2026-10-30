"""Authored command lists test scheduling arithmetic, never historical audio."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from extract_resources import extract
from pict_catalog import Unsupported
from snd_sequence import MAX_INPUT_BYTES, plan_manifest, plan_sequence
from test_audit_resources import sample


def sound(commands=None, rate_fixed=11025 << 16, base=69):
    # All bytes, sample values and note choices are authored test fixtures.
    commands = commands if commands is not None else [(40, 1, 69), (41, 1, 0)]
    offset = 12 + (len(commands) + 1) * 8
    table = struct.pack('>HHHIH', 1, 1, 5, 0, len(commands)+1)
    table += struct.pack('>HhI', 0x8050, 0, offset)
    table += b''.join(struct.pack('>HhI', *c) for c in commands)
    samples = bytes(range(16))
    header = struct.pack('>IIIIIBB', 0, len(samples), rate_fixed, 0, 0, 0, base)
    return table + header + samples


def fraction(value):
    return Fraction(value['numerator'], value['denominator'])


class SequencePlanTests(unittest.TestCase):
    def test_exact_half_millisecond_and_cumulative_fractional_frames(self):
        plan = plan_sequence(sound([(40, 1, 69)] * 1000), output_rate=11025)
        self.assertEqual(fraction(plan['commands'][1]['end_seconds']), Fraction(1, 2000))
        self.assertEqual(fraction(plan['commands'][1]['end_frame_position']), Fraction(441, 80))
        self.assertEqual(fraction(plan['duration_seconds']), Fraction(1, 2))
        self.assertEqual(fraction(plan['end_frame_position']), Fraction(11025, 2))
        self.assertEqual(plan['commands'][0]['start_seconds'], plan['commands'][0]['end_seconds'])
        for previous, following in zip(plan['commands'], plan['commands'][1:]):
            self.assertEqual(previous['end_frame_position'], following['start_frame_position'])

    def test_source_fixed_rate_and_pitched_request_are_preserved_without_rendering(self):
        data = sound([(40, 17, 74), (41, 5, 0)], rate_fixed=(11025 << 16)+32768)
        plan = plan_sequence(data)
        self.assertEqual(fraction(plan['sample']['source_rate']), Fraction(22051, 2))
        self.assertEqual(plan['sample']['base_frequency'], 69)
        self.assertEqual(plan['commands'][1]['requested_note'], 74)
        self.assertIn('does not stop', plan['commands'][1]['audible_stop'])
        self.assertEqual(plan['scope'], 'command-timing-plan-only')
        self.assertEqual(plan['source_sha256'], hashlib.sha256(data).hexdigest())
        self.assertNotIn('wav', plan)

    def test_zero_duration_and_canonical_null_command(self):
        plan = plan_sequence(sound([(0, 0, 0), (40, 0, 0), (41, 0, 0)]))
        self.assertEqual(fraction(plan['duration_seconds']), 0)
        self.assertEqual(plan['commands'][2]['requested_note'], 0)

    def test_unknown_flags_commands_and_ignored_parameter_variants_are_rejected(self):
        for command in [(0x8028, 1, 69), (0x4028, 1, 69), (3, 0, 0),
                        (81, 0, 0), (99, 0, 0), (40, -1, 69),
                        (41, 1, 3), (0, 1, 0)]:
            with self.subTest(command=command), self.assertRaises(Unsupported):
                plan_sequence(sound([command]))
        with self.assertRaisesRegex(ValueError, 'MIDI'):
            plan_sequence(sound([(40, 1, 128)]))

    def test_external_voice_and_unsupported_header_or_format_are_rejected(self):
        original = sound(); offset = struct.unpack_from('>I', original, 16)[0]
        mutations = [(4, '>H', 3), (6, '>I', 1), (offset, '>I', 123),
                     (offset+20, '>B', 0xff), (offset+21, '>B', 0),
                     (12, '>H', 80), (14, '>h', 2)]
        for position, fmt, value in mutations:
            changed = bytearray(original); struct.pack_into(fmt, changed, position, value)
            with self.subTest(position=position), self.assertRaises((Unsupported, ValueError)):
                plan_sequence(changed)
        changed = bytearray(original); struct.pack_into('>H', changed, 0, 2)
        with self.assertRaises((Unsupported, ValueError)):
            plan_sequence(changed)

    def test_bad_dimensions_offsets_and_truncation_are_rejected(self):
        original = sound(); offset = struct.unpack_from('>I', original, 16)[0]
        for changed in [original[:3], original[:-1], original[:25]]:
            with self.subTest(length=len(changed)), self.assertRaises(ValueError):
                plan_sequence(changed)
        for position, value in [(16, 12), (offset+4, 0), (offset+8, 0), (offset+12, 17)]:
            changed = bytearray(original); struct.pack_into('>I', changed, position, value)
            with self.subTest(position=position), self.assertRaises(ValueError):
                plan_sequence(changed)

    def test_duplicate_voice_and_timing_before_installation_are_rejected(self):
        with self.assertRaisesRegex(Unsupported, 'one offset soundCmd'):
            plan_sequence(sound([(0x8050, 0, 36)]))
        changed = bytearray(sound())
        first, second = bytes(changed[12:20]), bytes(changed[20:28])
        changed[12:20], changed[20:28] = second, first
        with self.assertRaisesRegex(Unsupported, 'before sampled voice'):
            plan_sequence(changed)

    def test_duration_frame_input_and_option_bounds_are_enforced(self):
        with self.assertRaisesRegex(ValueError, 'duration or frame bound'):
            plan_sequence(sound([(40, 2001, 69)]), max_seconds=1)
        with self.assertRaisesRegex(ValueError, 'duration or frame bound'):
            plan_sequence(sound([(40, 1, 69)]), output_rate=11025, max_frames=5)
        with self.assertRaisesRegex(ValueError, 'input bound'):
            plan_sequence(b'\0'*(MAX_INPUT_BYTES+1))
        for options in [{'output_rate': 0}, {'output_rate': True}, {'max_seconds': 61}, {'max_frames': 0}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                plan_sequence(sound(), **options)

    def test_manifest_plan_preserves_identity_and_rejects_overwrite_or_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'authored.rsrc'; data = sound()
            source.write_bytes(sample(b'snd ', data, 23)); extract(source, root/'extract')
            manifest = root/'extract/manifest.json'
            reports = plan_manifest(manifest, root/'plan', 23, output_rate=11025)
            self.assertEqual(reports[0]['id'], 23)
            self.assertEqual(reports[0]['source_sha256'], hashlib.sha256(data).hexdigest())
            self.assertIn('fork', reports[0])
            self.assertEqual(sorted(p.name for p in (root/'plan').iterdir()), ['report.json'])
            self.assertEqual(json.loads((root/'plan/report.json').read_text())['resources'], reports)
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                plan_manifest(manifest, root/'plan', 23)
            with self.assertRaisesRegex(ValueError, 'no matching'):
                plan_manifest(manifest, root/'missing', 24)
            self.assertFalse((root/'missing').exists())
            document = json.loads(manifest.read_text()); document['resources'][0]['sha256'] = '0'*64
            manifest.write_text(json.dumps(document))
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                plan_manifest(manifest, root/'changed', 23)
            self.assertFalse((root/'changed').exists())

    def test_failed_plan_and_public_checkout_destination_leave_no_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'authored.rsrc'
            source.write_bytes(sample(b'snd ', sound([(99, 1, 2)]), 23))
            extract(source, root/'extract'); manifest = root/'extract/manifest.json'
            with self.assertRaises(Unsupported):
                plan_manifest(manifest, root/'rejected', 23)
            self.assertFalse((root/'rejected').exists())
            with self.assertRaisesRegex(ValueError, 'local-generated'):
                plan_manifest(manifest, Path(__file__).resolve().parents[1]/'public-sound-plan', 23)
            with self.assertRaisesRegex(ValueError, 'resource ID'):
                plan_manifest(manifest, root/'bad-id', 32768)

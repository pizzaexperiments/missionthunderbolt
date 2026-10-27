import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_pict_independently import compare, verify
from test_pict_catalog import pict
from pict_catalog import decode


def authored_bitmap():
    rect = struct.pack('>hhhh', 0, 0, 4, 30)
    # One black pixel per row; two nonzero padding bits must not be painted.
    rows = b''.join(((1 << (31-y*7)) | 3).to_bytes(4, 'big') for y in range(4))
    return (b'\0\0'+rect+b'\0\x11\x02\xff'+b'\0\x90'+struct.pack('>H', 4)
            +rect+rect+rect+b'\0\0'+rows+b'\0\xff')


def authored_indexed_pixmap():
    rect = struct.pack('>hhhh', 0, 0, 4, 30)
    pixmap = struct.pack('>HHIIIHHHHIII', 0, 0, 0, 72 << 16, 72 << 16, 0, 1, 1, 1, 0, 0, 0)
    palette = struct.pack('>IHH', 0, 0, 1)+struct.pack('>HHHHHHHH', 0, 65535, 65535, 65535, 1, 0, 0, 0)
    rows = b''.join(((1 << (31-y*7)) | 3).to_bytes(4, 'big') for y in range(4))
    return (b'\0\0'+rect+b'\0\x11\x02\xff'+b'\0\x90'+struct.pack('>H', 0x8004)
            +rect+pixmap+palette+rect+rect+b'\0\0'+rows+b'\0\xff')


class IndependentPictTests(unittest.TestCase):
    def test_authored_bitmap_rows_ignore_padding_bits(self):
        width, height, pixels = decode(authored_bitmap())
        self.assertEqual((width, height), (30, 4))
        for y in range(4):
            black = [x for x in range(30) if pixels[(y*30+x)*3:(y*30+x+1)*3] == b'\0\0\0']
            self.assertEqual(black, [y*7])

    def test_authored_indexed_pixmap_matches_known_bitmap_pixels(self):
        self.assertEqual(decode(authored_indexed_pixmap()), decode(authored_bitmap()))

    @unittest.skipUnless(shutil.which(os.environ.get('GRAPHICSMAGICK_EXECUTABLE', 'gm')), 'optional GraphicsMagick decoder unavailable')
    def test_graphicsmagick_indexed_depths_and_padded_rows(self):
        tool = shutil.which(os.environ.get('GRAPHICSMAGICK_EXECUTABLE', 'gm'))
        for data in [pict(depth) for depth in (1, 4, 8)]+[authored_indexed_pixmap()]:
            self.assertEqual(compare(data, tool, 'graphicsmagick')['status'], 'exact')

    def test_graphicsmagick_adapter_uses_separate_bounded_commands(self):
        commands = []
        def reference(command, **kwargs):
            commands.append(command)
            self.assertEqual(kwargs['timeout'], 20)
            if command[1] == 'convert':
                pixels = decode(pict(1))[2]
                Path(command[-1][4:]).write_bytes(b''.join(bytes((v, v)) for v in pixels))
            return subprocess.CompletedProcess(command, 0, stdout='8 1', stderr='')
        with patch('verify_pict_independently.subprocess.run', side_effect=reference):
            self.assertEqual(compare(pict(1), 'synthetic-gm', 'graphicsmagick')['status'], 'exact')
        self.assertEqual([c[1] for c in commands], ['convert', 'identify'])
        self.assertTrue(all('-limit' in c for c in commands))

    @unittest.skipUnless(shutil.which('convert'), 'optional ImageMagick decoder unavailable')
    def test_authored_depths_against_real_independent_decoder(self):
        for depth in (1, 4, 8):
            with self.subTest(depth=depth):
                row = compare(pict(depth), shutil.which('convert'))
                self.assertEqual(row['status'], 'exact')
                self.assertEqual(row['different_pixels'], 0)
                self.assertEqual(row['maximum_channel_delta'], 0)

    def test_dimension_and_pixel_mismatches_are_not_tolerated(self):
        def reference(command, **kwargs):
            raw = Path(command[command.index('-write')+1][4:])
            raw.write_bytes(bytes(8*6))
            return subprocess.CompletedProcess(command, 0, stdout='8 1', stderr='')
        with patch('verify_pict_independently.subprocess.run', side_effect=reference):
            row = compare(pict(4), 'synthetic-reference')
        self.assertEqual(row['status'], 'pixel-mismatch')
        self.assertEqual(row['different_pixels'], 7)
        self.assertEqual(row['first_different_pixel'], [1, 0])
        with patch('verify_pict_independently.subprocess.run', return_value=subprocess.CompletedProcess([], 0, stdout='7 1')):
            self.assertEqual(compare(pict(4), 'synthetic-reference')['status'], 'dimension-mismatch')

    def test_failed_reference_is_recorded_and_output_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'report.json'
            record = {'fork': 'authored', 'id': 42, 'sha256': '0'*64}
            with patch('verify_pict_independently.subprocess.check_output', return_value='Synthetic reference 1\n'), patch('verify_pict_independently.compare', side_effect=subprocess.TimeoutExpired('test', 20)):
                report = verify([(record, pict(1))], output, 'synthetic-reference')
            self.assertEqual(report['counts']['failed'], 1)
            self.assertEqual(json.loads(output.read_text())['resources'][0]['reason'], 'TimeoutExpired')
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                verify([], output, 'synthetic-reference')
            repo = Path(__file__).resolve().parents[1]
            with self.assertRaisesRegex(ValueError, 'local-generated'):
                verify([], repo/'dist/unsafe-original-report.json', 'synthetic-reference')

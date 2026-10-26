import io
from pathlib import Path
import struct
import tempfile
import unittest
import wave
from test_audit_resources import sample
from extract_resources import extract
from sound_catalog import decode_sound,catalog
from pict_catalog import Unsupported


def snd(samples=b'\x00\x80\xff',encoding=0):
    commands=struct.pack('>HHHHHI',2,0,1,0x8051,0,14)
    header=struct.pack('>IIIIIBB',0,len(samples),22050<<16,0,len(samples),encoding,60)
    return commands+header+samples

class SoundTests(unittest.TestCase):
    def test_exact_pcm(self):
        wav,meta=decode_sound(snd())
        with wave.open(io.BytesIO(wav),'rb') as w:
            self.assertEqual((w.getnchannels(),w.getsampwidth(),w.getframerate()),(1,1,22050))
            self.assertEqual(w.readframes(3),b'\0\x80\xff')
        self.assertEqual(meta['loop_end'],3)
    def test_truncated_and_compressed(self):
        with self.assertRaises(ValueError):decode_sound(snd()[:-1])
        with self.assertRaises(Unsupported):decode_sound(snd(encoding=0xfe))
    def test_extended_16_bit_endian(self):
        header=bytearray(64);struct.pack_into('>IIIIIBB',header,0,0,1,11025<<16,0,2,0xff,60)
        struct.pack_into('>I',header,22,2);struct.pack_into('>H',header,48,16)
        data=snd()[:14]+header+b'\x01\x02\xfe\xfd'
        wav,meta=decode_sound(data)
        with wave.open(io.BytesIO(wav),'rb') as w:self.assertEqual(w.readframes(2),b'\x02\x01\xfd\xfe')
        self.assertEqual(meta['sample_bits'],16)
    def test_catalog_keeps_resource_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'synthetic.rsrc';source.write_bytes(sample(b'snd ',snd(),7))
            extract(source,root/'extract');report=catalog(root/'extract/manifest.json',root/'audio')
            self.assertEqual(report[0]['id'],7);self.assertEqual(report[0]['status'],'converted')

class SoundSequenceTests(unittest.TestCase):
    @staticmethod
    def sequence():
        # Authored sequence: one offset sample followed by two timed commands.
        header=struct.pack('>HHHI',1,1,5,0)
        commands=struct.pack('>H',3)+struct.pack('>HhI',0x8050,0,36)
        commands+=struct.pack('>HhI',40,120,64)+struct.pack('>HhI',41,15,0)
        sample_header=struct.pack('>IIIIIBB',0,3,11025<<16,0,3,0,64)
        return header+commands+sample_header+b'\x10\x80\xf0'
    def test_sample_preview_preserves_sequence(self):
        from sound_catalog import inspect_commands
        data=self.sequence();listing=inspect_commands(data)
        self.assertEqual([c['name'] for c in listing['commands']],['soundCmd','freqDurationCmd','restCmd'])
        self.assertEqual(listing['commands'][1]['param1'],120)
        self.assertEqual(listing['commands'][1]['param2'],64)
        self.assertTrue(listing['commands'][0]['data_offset'])
        self.assertEqual(listing['modifiers'],[{'synthesizer':5,'initialization':0}])
        with self.assertRaises(Unsupported):decode_sound(data)
        wav,meta=decode_sound(data,sample_only=True)
        self.assertEqual(meta['playback_scope'],'sample-only')
        with wave.open(io.BytesIO(wav),'rb') as w:self.assertEqual(w.readframes(3),b'\x10\x80\xf0')
    def test_catalog_distinguishes_sample_from_sequence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'synthetic.rsrc';source.write_bytes(sample(b'snd ',self.sequence(),11))
            extract(source,root/'extract');report=catalog(root/'extract/manifest.json',root/'audio')
            self.assertEqual(report[0]['status'],'sample-only')
            self.assertEqual(len(report[0]['command_list']['commands']),3)
    def test_unknown_commands_and_bad_offsets_still_fail(self):
        from sound_catalog import inspect_commands
        data=bytearray(self.sequence());struct.pack_into('>H',data,20,99)
        self.assertEqual(inspect_commands(data)['commands'][1]['name'],'unknown')
        with self.assertRaises(Unsupported):decode_sound(data,sample_only=True)
        data=bytearray(self.sequence());struct.pack_into('>I',data,16,12)
        with self.assertRaises(ValueError):decode_sound(data,sample_only=True)
        with self.assertRaises(ValueError):inspect_commands(self.sequence()[:30])
    def test_signed_param1_and_unsupported_synthesizer(self):
        from sound_catalog import inspect_commands
        data=bytearray(self.sequence());struct.pack_into('>h',data,22,-1)
        self.assertEqual(inspect_commands(data)['commands'][1]['param1'],-1)
        data=bytearray(self.sequence());struct.pack_into('>H',data,4,3)
        with self.assertRaises(Unsupported):decode_sound(data,sample_only=True)

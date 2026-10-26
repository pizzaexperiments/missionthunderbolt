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

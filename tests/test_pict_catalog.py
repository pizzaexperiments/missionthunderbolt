from pathlib import Path
import struct
import tempfile
import unittest
from test_audit_resources import sample
from pict_catalog import decode, png, unpackbits, Unsupported, catalog
from extract_resources import extract


def pict(depth):
    rect=struct.pack('>hhhh',0,0,1,8)
    header=b'\0\0'+rect+b'\0\x11\x02\xff'
    count=1<<depth
    pm=struct.pack('>HHIIIHHHHIII',0,0,0,72<<16,72<<16,0,depth,1,depth,0,0,0)
    palette=struct.pack('>IHH',0,0,count-1)+b''.join(struct.pack('>HHHH',i,i*65535//(count-1),0,0) for i in range(count))
    stride=depth
    raw={1:b'\x55',4:b'\x01\x23\x45\x67',8:bytes(range(8))}[depth]
    if stride>=8: raw=bytes([len(raw)+1,len(raw)-1])+raw
    data=header+b'\0\x98'+struct.pack('>H',0x8000|stride)+rect+pm+palette+rect+rect+b'\0\0'+raw
    if len(data)%2:data+=b'\0'
    return data+b'\0\xff'

class PictTests(unittest.TestCase):
    def test_indexed_depths(self):
        for depth in (1,4,8):
            w,h,pixels=decode(pict(depth))
            self.assertEqual((w,h),(8,1))
            self.assertEqual(pixels[:3],bytes((0,0,0)))
            expected=255 if depth==1 else 7*65535//((1<<depth)-1)>>8
            self.assertEqual(pixels[-3:],bytes((expected,0,0)))
            self.assertTrue(png(w,h,pixels).startswith(b'\x89PNG'))

    def test_packbits_validation(self):
        self.assertEqual(unpackbits(b'\xfeA',3),b'AAA')
        for data in (b'\xfeA',b'\x02ab',b'\x00a'):
            with self.assertRaises(ValueError): unpackbits(data,2)

    def test_truncated_and_unsupported(self):
        with self.assertRaises(ValueError):decode(pict(8)[:-1])
        b=bytearray(pict(1)); b[14:16]=b'\x12\x34'
        with self.assertRaises(Unsupported):decode(bytes(b))

    def test_local_catalog_and_source_mapping(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); source=root/'synthetic.rsrc'
            source.write_bytes(sample(b'PICT',pict(4),-23))
            extract(source,root/'extracted')
            report=catalog(root/'extracted/manifest.json',root/'catalog')
            self.assertEqual(report[0]['status'],'decoded')
            self.assertEqual(report[0]['id'],-23)
            self.assertTrue((root/'catalog/contact-sheet.png').is_file())
            self.assertEqual(json.loads((root/'catalog/report.json').read_text())['resources'],report)

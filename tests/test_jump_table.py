import struct
import unittest
from test_audit_resources import sample
from map_jump_table import map_jumps

class JumpTableTests(unittest.TestCase):
    def fixture(self):
        code0=struct.pack('>IIIIHHHH',40,64,8,32,0,0x3f3c,1,0xa9f0)
        code1=struct.pack('>HH',0,1)+b'\0\0'
        return {0:code0,1:code1}
    def test_resource_relative_mapping(self):
        result=map_jumps(self.fixture());entry=result['entries'][0]
        self.assertEqual((entry['segment'],entry['resource_offset'],entry['a5_displacement']),(1,4,34))
        self.assertFalse(result['runtime_load_addresses_known'])
    def test_unknown_stub_and_bad_target_rejected(self):
        for index in (18,20,22):
            segments=self.fixture();b=bytearray(segments[0]);b[index]^=1;segments[0]=bytes(b)
            with self.assertRaises(ValueError):map_jumps(segments)
    def test_header_count_mismatch(self):
        segments=self.fixture();segments[1]=struct.pack('>HH',0,2)+b'\0\0'
        with self.assertRaises(ValueError):map_jumps(segments)

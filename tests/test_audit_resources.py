import importlib.util
import pathlib
import struct
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import audit_resources as a


def sample(typ=b'TEST', payload=b'abc', rid=42):
    data = struct.pack('>I', len(payload)) + payload
    mapping = bytearray(50)
    struct.pack_into('>HH', mapping, 24, 28, 50)
    struct.pack_into('>H4sHHhH', mapping, 28, 0, typ, 0, 10, rid, 0xffff)
    header = struct.pack('>IIII', 256, 256 + len(data), len(data), len(mapping))
    mapping[:16] = header
    return header + bytes(240) + data + mapping

class ForkTests(unittest.TestCase):
    def test_valid(self):
        x = list(a.parse_fork(sample()))
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0][:3], ('TEST', 42, 3))

    def test_truncated(self):
        for x in (b'', b'\0' * 18, sample()[:-1]):
            with self.assertRaises(ValueError): list(a.parse_fork(x))

    def test_invalid_size(self):
        b = bytearray(sample()); struct.pack_into('>I', b, 256, 999)
        with self.assertRaises(ValueError): list(a.parse_fork(b))

    def test_invalid_type_count(self):
        b = bytearray(sample()); m = a.u32(b, 4); struct.pack_into('>H', b, m + 28, 400)
        with self.assertRaises(ValueError): list(a.parse_fork(b))

    def test_empty_type_list(self):
        b = bytearray(sample()); m = a.u32(b, 4); struct.pack_into('>H', b, m + 28, 0xffff)
        self.assertEqual(list(a.resources(b)), [])

    def test_signed_resource_id(self):
        self.assertEqual(list(a.resources(sample(rid=-128)))[0][1], -128)

    def test_overlapping_sections(self):
        b = bytearray(sample()); struct.pack_into('>I', b, 4, 256)
        with self.assertRaises(ValueError): list(a.resources(b))

    def test_reference_before_table(self):
        b = bytearray(sample()); m = a.u32(b, 4); struct.pack_into('>H', b, m + 36, 0)
        with self.assertRaises(ValueError): list(a.resources(b))

if __name__ == '__main__': unittest.main()

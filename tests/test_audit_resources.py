import importlib.util,pathlib,struct,unittest
path=pathlib.Path(__file__).resolve().parents[1]/"scripts"/"audit_resources.py"
spec=importlib.util.spec_from_file_location("audit_resources",path)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def sample():
    b=bytearray(512)
    struct.pack_into(">IIII",b,0,256,32,7,200)
    struct.pack_into(">H",b,56,28)
    struct.pack_into(">H",b,60,0)
    b[62:66]=b"TEST"
    struct.pack_into(">HH",b,66,0,10)
    struct.pack_into(">h",b,70,42)
    struct.pack_into(">I",b,256,3)
    b[260:263]=b"abc"
    return bytes(b)
class ForkTests(unittest.TestCase):
    def test_valid(self):
        x=list(a.parse_fork(sample()))
        self.assertEqual(len(x),1)
        self.assertEqual(x[0][:3],("TEST",42,3))
    def test_truncated(self):
        for x in (b"",b"\0"*18,sample()[:262]):
            with self.assertRaises(ValueError): list(a.parse_fork(x))
    def test_invalid_size(self):
        b=bytearray(sample());struct.pack_into(">I",b,256,999)
        with self.assertRaises(ValueError): list(a.parse_fork(b))
    def test_invalid_type_count(self):
        b=bytearray(sample());struct.pack_into(">H",b,60,400)
        with self.assertRaises(ValueError): list(a.parse_fork(b))
if __name__=="__main__": unittest.main()

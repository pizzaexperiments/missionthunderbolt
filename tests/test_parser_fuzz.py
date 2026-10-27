"""Deterministic synthetic mutation corpus; original bytes are never committed."""
import random
import unittest
from test_audit_resources import sample
from test_extract_resources import double
from test_pict_catalog import pict
from test_sound_catalog import snd
from audit_resources import resources
from extract_resources import apple_resource_fork
from pict_catalog import decode
from sound_catalog import decode_sound

class ParserMutationTests(unittest.TestCase):
    def test_seeded_mutations_and_truncations(self):
        rng=random.Random(1701)
        cases=[(lambda data:list(resources(data)),sample()),(apple_resource_fork,double(sample())),
               (decode,pict(8)),(decode_sound,snd())]
        executed=0
        for parser,valid in cases:
            parser(valid)
            for n in range(len(valid)):
                try:parser(valid[:n])
                except ValueError:pass
                executed+=1
            for _ in range(250):
                data=bytearray(valid);index=rng.randrange(len(data));data[index]^=1<<rng.randrange(8)
                try:parser(bytes(data))
                except ValueError:pass
                executed+=1
        self.assertGreater(executed,1000)

#!/usr/bin/env python3
"""Optional Atheris target for in-memory parsers; seed with authored fixtures only."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests')]


def seed_corpus(destination):
    from test_audit_resources import sample
    from test_extract_resources import double
    from test_pict_catalog import pict
    from test_sound_catalog import snd,SoundSequenceTests
    destination=destination.resolve()
    if destination.is_relative_to(ROOT) and not destination.is_relative_to(ROOT/'dist'):
        raise ValueError('keep generated fuzz corpora under dist/ or outside the checkout')
    destination.mkdir(parents=True,exist_ok=False)
    cases=[bytes([i]) for i in range(4)]
    cases.extend([b'\0'+sample(),b'\1'+double(sample())])
    cases.extend(b'\2'+pict(depth) for depth in (1,4,8))
    cases.extend([b'\3'+snd(),b'\3'+SoundSequenceTests.sequence()])
    for index,data in enumerate(cases):(destination/f'seed_{index:02d}').write_bytes(data)
    print(f'Created {len(cases)} synthetic seeds; no original inputs read')


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--seed-corpus':
        seed_corpus(Path(sys.argv[2]));sys.exit(0)
    import atheris
    with atheris.instrument_imports():
        from audit_resources import resources
        from extract_resources import apple_resource_fork
        from pict_catalog import decode
        from sound_catalog import decode_sound

    @atheris.instrument_func
    def fuzz_one(data):
        if not data:return
        selector=data[0]%4;payload=data[1:]
        try:
            if selector==0:
                parsed=list(resources(payload))
                assert len({(kind,rid) for kind,rid,_ in parsed})==len(parsed)
                for kind,rid,body in parsed:
                    assert len(kind)==4 and -32768<=rid<=32767 and len(body)<=len(payload)
            elif selector==1:
                fork=apple_resource_fork(payload)
                assert len(fork)<=len(payload)
            elif selector==2:
                width,height,pixels=decode(payload)
                assert width>0 and height>0 and len(pixels)==width*height*3
            else:
                wav,meta=decode_sound(payload,sample_only=True)
                assert len(wav)==44+meta['frames']*meta['channels']*(meta['sample_bits']//8)
                assert wav[:4]==b'RIFF' and wav[8:12]==b'WAVE'
        except ValueError:
            pass  # Documented malformed/unsupported input; other exceptions must fail.

    atheris.Setup(sys.argv,fuzz_one)
    atheris.Fuzz()

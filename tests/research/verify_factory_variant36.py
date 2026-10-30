#!/usr/bin/env python3
"""Original variant 36 draw overwrite and fallthrough to variant 31 fields."""
import argparse
import json
from pathlib import Path
import random
import struct
from verify_factory_variant_draws import verify


def cases():
    rng=random.Random(2608);index=0
    for variant in (36,31):
        for level in (-32768,-3277,-3,-1,0,1,32767):
            for word in (0,1,32767,32768,65535):
                for profile in range(3):
                    table=bytearray(rng.randrange(256) for _ in range(76*112));kind=72 if profile==1 else variant
                    for i in range(76):
                        p=i*112;struct.pack_into('>H',table,p,kind);table[p+20]=(table[p+20]&223)|(32 if profile!=2 else 0)
                        table[p+51]=2;struct.pack_into('>II',table,p+60,0x110000,0x110100)
                        table[p+11]=255;struct.pack_into('>H',table,p+14,word)
                    children={}
                    for i in range(2):
                        child=bytearray(32);child[1]=42+i;child[18]=1;struct.pack_into('>H',child,16,2+i*3);children[0x110000+i*0x100]=bytes(child)
                    yield {'mode':profile,'seed':501+index,'fallback':42,'last':123,'global':[0,128,255][profile],
                           'warmup':32 if profile==0 else 0,'record':bytes([0xa5])*112,'variant':variant,'level':level,
                           'flag39':0,'table':bytes(table),'children':children,'thresholds':[-1]*256,
                           'mode_word':0,'base_long':0}
                    index+=1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep evidence private')
    report=verify(a.manifest,a.native_driver,case_stream=cases())
    report['scope']='Original variant 36 bound-20 overwrite then variant-31 fallthrough, common RNG tail and actual follow-up; authored supplied resources'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} variant-36/control cases, {report["variant_prefix_draws"]} prefix draws, {report["rng_draws"]} total draws and {report["executed_followups"]} callbacks')


if __name__=='__main__':main()

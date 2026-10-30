#!/usr/bin/env python3
"""Check supported supplied-allocation child factory bodies, not whole-game behavior."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_child_record_prefix import SOURCES, cases as prefix_cases, forced_table, original, template
from verify_rng_cpu import manifest_inputs

EXCLUDED={36,37,70,77,137,138,166}
REQUIRED={'count_draw','word_add','word_subtract','word_signed_clamp',
          'byte_increment_one','byte_increment_random','byte_decrement_one',
          'byte_decrement_random','byte_signed_clamp','type39','type63','type62',
          'type62_negative','type62_high','type81_141','type109','type108','type100',
          'type114_116','type25','type25_low','type25_middle','type25_other',
          'type127','type129','type129_nonzero','type129_zero','flag24_bit3',
          'byte13','flag25_bit2'}


def cases():
    for c in prefix_cases():
        yield dict(c,level=0,factor=0x8001)
    def make(kind,level=0,variant=0,count=1,word=65535,byte=1,flags=0,bound=3,factor=0x8001,values=None,seed=42):
        t=bytearray(template(kind,count,word,byte,flags));struct.pack_into('>H',t,22,bound)
        fallback,shuffle=forced_table(values) if values is not None else (42,[0]*100)
        return {'template':bytes(t),'variant':variant,'mode':int(values is not None),
                'seed':seed,'fallback':fallback,'last':0x89abcdef,'warmup':seed%5,
                'shuffle':shuffle,'record':b'\xcc'*56,'level':level,'factor':factor}
    # Every supported dispatch-table entry, plus unsigned range boundaries.
    for kind in [0,1,24,*range(25,168),168,32767,32768,65535]:
        if kind in EXCLUDED:continue
        for profile in range(2):
            yield make(kind,variant=kind%137,level=14 if profile else -4,
                       count=32767 if profile else 1,flags=32 if profile else 0,seed=kind+profile)
    levels=(-32768,-32767,-11,-10,-6,-5,-4,-1,0,1,4,5,9,10,14,15,16,19,20,21,32766,32767)
    for level in levels:
        for byte in (0,1,3,4,6,7,127,128,255):yield make(25,level=level,byte=byte)
        for raw in (0,5,10):
            c=make(62,level=level,values=[raw,4]);c['warmup']=0;yield c
    for kind in (114,116):
        for bound in (0,1,2,32767,32768,65535):
            for raw in (0,32767):
                c=make(kind,bound=bound,values=[raw]);c['warmup']=0;yield c
    for factor in (0,1,32767,32768,65534,65535):
        for raw in range(5):
            c=make(127,factor=factor,values=[raw]);c['warmup']=0;yield c
            # Slot42 is both copy source and later factor source here.
            c=make(127,variant=42,factor=factor,word=factor,values=[raw]);c['warmup']=0;yield c
    for raw in (0,1,3):
        c=make(129,values=[raw]);c['warmup']=0;yield c
    c=make(62,count=3,word=32768,byte=1,flags=32,values=[2,1,0,9,1,0,0,2,0,4]);c['warmup']=0;yield c


def verify(manifest,driver):
    sources={}
    for resource,data in manifest_inputs(manifest,'CODE'):
        sid=resource['id']
        if sid not in SOURCES:continue
        if sid in sources or hashlib.sha256(data).hexdigest()!=SOURCES[sid]:raise ValueError('ambiguous/unsupported CODE source')
        sources[sid]=data
    if set(sources)!=set(SOURCES):raise ValueError('required CODE sources missing')
    inputs=[];wanted=[];count=0;draws=0;maximum=0;coverage=Counter();digest=hashlib.sha256();types=set()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native output count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:
                aa,bb=a.split(),b.split();token=next((j for j,(x,y) in enumerate(zip(aa,bb)) if x!=y),min(len(aa),len(bb)))
                raise AssertionError(f'child factory mismatch case {count-len(wanted)+i}, token {token}')
        inputs.clear();wanted.clear()
    for c in cases():
        types.add(struct.unpack_from('>H',c['template'])[0])
        line,n,blocks=original(sources,c,factory=True)
        wanted.append(line);count+=1;draws+=n;maximum=max(maximum,n);coverage.update(blocks);digest.update((line+'\n').encode())
        inputs.append(' '.join(str(c[k]) for k in ('mode','seed','fallback','last','warmup','variant','level','factor'))+' '+c['record'].hex()+' '+c['template'].hex()+
                      (' '+' '.join(map(str,c['shuffle'])) if c['mode'] else ''))
        if len(inputs)==128:flush()
    flush()
    if set(coverage)!=REQUIRED:raise AssertionError(f'arithmetic/type block coverage differs: {set(coverage)^REQUIRED}')
    if maximum!=10:raise AssertionError('maximum ten-draw path not covered')
    if not (set(range(25,168))-EXCLUDED)<=types:raise AssertionError('supported table entry not covered')
    import unicorn
    return {'schema':1,'source_sha256':SOURCES,'unicorn_version':unicorn.__version__,
            'cases':count,'rng_draws':draws,'maximum_draws_per_case':maximum,
            'tested_raw_types':sorted(types),'executed_blocks':dict(sorted(coverage.items())),
            'result_sha256':digest.hexdigest(),
            'scope':'CODE9 0x484e..0x4cd8 supplied allocation with authored137x56templates; all supported dispatch entries, no allocator/epilogue/recursive or external-context types/gameplay'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} child factory cases, {report["rng_draws"]} draws and {len(report["executed_blocks"])} blocks')


if __name__=='__main__':main()

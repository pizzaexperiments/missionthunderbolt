#!/usr/bin/env python3
"""Original-instruction checks for explicitly supplied authored child contexts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_child_record_prefix import SOURCES, forced_table, original, template
from verify_rng_cpu import manifest_inputs

REQUIRED={'context_type37','lookup_nonnegative','lookup_low','lookup_lowest',
          'lookup_high','lookup_middle','lookup_eligible','lookup_replacement',
          'context_type77','level_positive','level_nonpositive','context_counter'}


def cases():
    def make(kind,*,level=0,variant=0,word=65535,count=1,byte=1,flags=0,byte7=128,word16=65535,
             lookup_value=255,factor_word=0x8001,counter=65535,address_base=0xfffffff0,values=None,seed=42):
        t=bytearray(template(kind,count,word,byte,flags));t[7]=byte7;struct.pack_into('>H',t,16,word16)
        fallback,shuffle=forced_table(values) if values is not None else (42,[0]*100)
        context={'lookup':bytes([lookup_value])*50,'factor_word':factor_word,'counter':counter,'address_base':address_base}
        c={'template':bytes(t),'variant':variant,'mode':int(values is not None),'seed':seed,'fallback':fallback,
           'last':0x89abcdef,'warmup':0,'shuffle':shuffle,'record':b'\xcc'*56,'level':level,'factor':0x8001}
        return c,context
    # All raw lookup bytes and every table index, with both optional draw outcomes.
    for value in range(256):
        index=value%50
        for draws in ([index,0,0],[index,0,2],[index,4]):
            c,context=make(37,variant=value%137,word=(0,32767,32768,65535)[value%4],lookup_value=value,values=draws)
            lookup=bytearray([2]*50);lookup[index]=value;context['lookup']=bytes(lookup)
            yield c,context
    # Signed multiplier, signed byte and caller-word edge combinations.
    for level in (-32768,-129,-128,-1,0,1,127,128,255,256,32767):
        for factor in (0,1,32767,32768,65535):
            for byte in (0,1,127,128,255):
                for old_word in (0,65535):
                    yield make(77,level=level,factor_word=factor,byte7=byte,word16=old_word)
    for kind in (137,138):
        for counter in (0,1,32767,32768,65535):
            for base in (0,1,0x7fffffff,0xfffffff0,0xffffffff):
                for raw in (0,1,499):
                    yield make(kind,counter=counter,address_base=base,values=[raw])
    # Initialization plus changing prefix draws remains connected to each context.
    for kind in (37,77,137,138):
        for seed in range(64):
            yield make(kind,seed=seed,count=32767 if seed%2 else 1,flags=32,
                       byte=(1,127,128,255)[seed%4],level=seed-32,lookup_value=seed,
                       counter=seed*1024,address_base=(seed*0x10000001)&0xffffffff)
    # Full eight-draw prefix followed by lookup, chance and count replacement.
    c,context=make(37,variant=136,count=3,word=32768,byte=1,flags=32,lookup_value=255,
                   values=[2,1,0,9,1,0,0,2,49,0,2])
    context['lookup']=bytes([2]*49+[255]);yield c,context


def verify(manifest,driver):
    sources={}
    for resource,data in manifest_inputs(manifest,'CODE'):
        sid=resource['id']
        if sid not in SOURCES:continue
        if sid in sources or hashlib.sha256(data).hexdigest()!=SOURCES[sid]:raise ValueError('ambiguous/unsupported CODE source')
        sources[sid]=data
    if set(sources)!=set(SOURCES):raise ValueError('required CODE sources missing')
    inputs=[];wanted=[];count=0;draws=0;maximum=0;coverage=Counter();types=Counter();digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native output count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:
                aa,bb=a.split(),b.split();token=next((j for j,(x,y) in enumerate(zip(aa,bb)) if x!=y),min(len(aa),len(bb)))
                raise AssertionError(f'child context mismatch case {count-len(wanted)+i}, token {token}')
        inputs.clear();wanted.clear()
    for c,context in cases():
        line,n,blocks=original(sources,c,factory=True,context=context)
        wanted.append(line);count+=1;draws+=n;maximum=max(maximum,n);coverage.update(blocks)
        types[struct.unpack_from('>H',c['template'])[0]]+=1;digest.update((line+'\n').encode())
        inputs.append(' '.join(str(c[k]) for k in ('mode','seed','fallback','last','warmup','variant','level','factor'))+
                      ' '+context['lookup'].hex()+' '+' '.join(str(context[k]) for k in ('factor_word','counter','address_base'))+
                      ' '+c['record'].hex()+' '+c['template'].hex()+(' '+' '.join(map(str,c['shuffle'])) if c['mode'] else ''))
        if len(inputs)==128:flush()
    flush()
    if not REQUIRED<=set(coverage):raise AssertionError('required context branch not executed')
    if maximum!=11:raise AssertionError('maximum eleven-draw path not executed')
    import unicorn
    return {'schema':1,'source_sha256':SOURCES,'unicorn_version':unicorn.__version__,'cases':count,
            'rng_draws':draws,'maximum_draws_per_case':maximum,'type_cases':dict(sorted(types.items())),
            'lookup_byte_values':256,'executed_blocks':dict(sorted(coverage.items())),'result_sha256':digest.hexdigest(),
            'scope':'CODE9 supplied-allocation 0x484e..0x4cd8 with explicitly authored contexts for raw types37/77/137/138; complete record/RNG/ordered trace/counter compared, all new inputs/guards checked; allocator/recursion/external helpers/gameplay excluded'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} child-context cases, {report["rng_draws"]} draws, maximum {report["maximum_draws_per_case"]}')


if __name__=='__main__':main()

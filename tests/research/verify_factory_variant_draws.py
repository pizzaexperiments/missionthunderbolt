#!/usr/bin/env python3
"""Original factory variants 60/67 with prefix RNG and raw global-long wrap."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_factory_mode_variant import ModeExecution
from verify_finalized_template_factory import ALL_SOURCES
from verify_record_template_factory import original,PREFIX_BOUNDS
from verify_rng_cpu import manifest_inputs


def cases():
    rng=random.Random(2508);index=0
    for variant in (60,67,79):
        for mode in (-32768,-1,0,1,2,3,4,32767):
            for base in (0,1,0x7fffffff,0xfffffff8,0xffffffff):
                for word in (0,1,32767,32768,65535):
                    for profile in range(3):
                        table=bytearray(rng.randrange(256) for _ in range(76*112));kind=72 if profile==1 else variant
                        if kind>75:kind=0
                        for i in range(76):
                            p=i*112;struct.pack_into('>H',table,p,kind);table[p+20]=(table[p+20]&223)|(32 if profile!=2 else 0)
                            table[p+51]=2;struct.pack_into('>II',table,p+60,0x110000,0x110100)
                            table[p+2]=[0,127,255][index%3];table[p+8]=[255,127,0][index%3]
                            struct.pack_into('>H',table,p+14,word);struct.pack_into('>I',table,p+4,base)
                        children={}
                        for i in range(2):
                            child=bytearray(32);child[1]=42+i;child[18]=1;struct.pack_into('>H',child,16,2+i*3);children[0x110000+i*0x100]=bytes(child)
                        yield {'mode':profile,'seed':42+index,'fallback':42,'last':123,'global':[0,128,255][profile],
                               'warmup':32 if profile==0 else 0,'record':bytes([0xa5])*112,'variant':variant,'level':-3,
                               'flag39':0,'table':bytes(table),'children':children,'thresholds':[-1 if b%2 else 1 for b in range(256)],
                               'mode_word':mode,'base_long':base}
                        index+=1


def verify(manifest,driver,case_stream=None):
    sources={r['id']:d for r,d in manifest_inputs(manifest,'CODE') if r['id'] in ALL_SOURCES}
    if set(sources)!=set(ALL_SOURCES) or any(hashlib.sha256(sources[s]).hexdigest()!=h for s,h in ALL_SOURCES.items()):raise ValueError('unsupported CODE')
    inputs=[];wanted=[];count=0;draws=0;callbacks=0;prefixes=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:
                aa,bb=a.split(),b.split();token=next((j for j,(x,y) in enumerate(zip(aa,bb)) if x!=y),min(len(aa),len(bb)))
                raise AssertionError(f'variant-prefix mismatch {count-len(wanted)+i}, token {token}')
        inputs.clear();wanted.clear()
    for c in (cases() if case_stream is None else case_stream):
        execution=ModeExecution(sources,c);line,z,n,f=original(sources,c,followup=execution)
        wanted.append(line);count+=1;draws+=n;callbacks+=f;prefixes+=int(c['variant'] in PREFIX_BOUNDS);digest.update((line+'\n').encode())
        keys=('mode','seed','fallback','last','global','warmup','variant')
        text=' '.join(str(c[k]) for k in keys)+f' {c["level"]&65535} {c["flag39"]} {c["mode_word"]&65535} {c["base_long"]} '+c['record'].hex()+' '+c['table'].hex()
        text+=' '+b''.join(struct.pack('>h',v) for v in c['thresholds']).hex()+' '+str(len(c['children']))
        text+=''.join(f' {i} '+b.hex() for i,b in sorted(c['children'].items()));inputs.append(text)
        if len(inputs)==16:flush()
    flush()
    import unicorn
    return {'schema':1,'source_sha256':ALL_SOURCES,'unicorn_version':unicorn.__version__,'cases':count,
            'rng_draws':draws,'variant_prefix_draws':prefixes,'executed_followups':callbacks,'result_sha256':digest.hexdigest(),
            'scope':'Original variants 60/67 prefix RNG, mode/global-long effects, common tail and actual follow-up; authored supplied allocation/resources/children'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} prefix-variant cases, {report["variant_prefix_draws"]} prefix draws, {report["rng_draws"]} total draws and {report["executed_followups"]} callbacks')


if __name__=='__main__':main()

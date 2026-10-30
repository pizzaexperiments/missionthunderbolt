#!/usr/bin/env python3
"""Original supplied-allocation factory executing its actual CODE 7 follow-up."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_record_template_factory import SOURCES,SUPPORTED,original
from verify_record_followup import SHA
from verify_grid_selector import A5
from verify_rng_cpu import manifest_inputs

BASE7,META=0x50000,0x100000
ALL_SOURCES={**SOURCES,7:SHA}


def cases():
    rng=random.Random(2308)
    for variant in SUPPORTED+[89,32767]:
        for level in (-32768,-3,0,1,32767):
            for profile in range(3):
                count=(variant+level+profile)%14
                table=bytearray(rng.randrange(256) for _ in range(76*112))
                for i in range(76):
                    kind=i if profile==0 else (i*7+3)%76 if profile==1 else 72
                    struct.pack_into('>H',table,i*112,kind);table[i*112+51]=count
                    table[i*112+20]=(table[i*112+20]&223)|(32 if profile else 0)
                    for j in range(count):struct.pack_into('>I',table,i*112+60+j*4,0x110000+j*0x100)
                children={}
                for i in range(count):
                    child=bytearray(rng.randrange(256) for _ in range(32));child[18]=i%3
                    struct.pack_into('>h',child,8,0 if i%2==0 else -1)
                    struct.pack_into('>H',child,16,[2,5,5,32767,32768,1,0][i%7]);child[24]=2 if i%5==0 else 0;child[25]=0
                    children[0x110000+i*0x100]=bytes(child)
                mode=(variant+profile)%3
                yield {'mode':mode,'seed':42+variant,'fallback':42,'last':123,'global':[0,128,255][profile],
                       'warmup':32 if mode==0 else 0,'record':bytes([0xa5])*112,'variant':variant,'level':level,
                       'flag39':255 if profile else 0,'table':bytes(table),'children':children,
                       'thresholds':[[-32768,-1,0,32767][i%4] for i in range(256)]}


class FollowupExecution:
    def __init__(self,sources,c):self.sources=sources;self.c=c;self.calls=0
    def prepare(self,uc):
        uc.mem_write(BASE7,self.sources[7]);uc.mem_write(A5+0xb92,b'\x4e\xf9'+struct.pack('>I',BASE7+9972))
        metadata=bytearray(b'\x5a'*(256*56))
        for b,value in enumerate(self.c['thresholds']):struct.pack_into('>h',metadata,((b+128)&255)*56+8,value)
        self.metadata=bytes(metadata);uc.mem_write(META-16,b'\xcc'*16+self.metadata+b'\xcc'*16)
        uc.mem_write(A5-0x2626,struct.pack('>I',META+128*56))
        for identity,child in self.c['children'].items():uc.mem_write(identity-16,b'\xcc'*16+child+b'\xcc'*16)
    def service(self,uc,address):
        if address!=A5+0xb92:raise AssertionError('unmodeled finalized factory service')
        self.calls+=1
    def inspect(self,uc,observed):
        if self.calls!=observed['followup']:raise AssertionError('follow-up call count')
        if bytes(uc.mem_read(META-16,len(self.metadata)+32))!=b'\xcc'*16+self.metadata+b'\xcc'*16:raise AssertionError('threshold metadata/guards')
        if bytes(uc.mem_read(A5-0x2626,4))!=struct.pack('>I',META+128*56):raise AssertionError('threshold pointer')
        for identity,child in self.c['children'].items():
            if bytes(uc.mem_read(identity-16,64))!=b'\xcc'*16+child+b'\xcc'*16:raise AssertionError('child changed/guard')


def verify(manifest,driver):
    sources={r['id']:d for r,d in manifest_inputs(manifest,'CODE') if r['id'] in ALL_SOURCES}
    if set(sources)!=set(ALL_SOURCES) or any(hashlib.sha256(sources[s]).hexdigest()!=h for s,h in ALL_SOURCES.items()):raise ValueError('unsupported CODE')
    inputs=[];wanted=[];count=0;draws=0;zero=0;calls=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:raise AssertionError(f'finalized factory mismatch {count-len(wanted)+i}')
        inputs.clear();wanted.clear()
    for c in cases():
        followup=FollowupExecution(sources,c)
        line,z,n,f=original(sources,c,followup=followup);wanted.append(line);count+=1;zero+=z;draws+=n;calls+=f;digest.update((line+'\n').encode())
        keys=('mode','seed','fallback','last','global','warmup','variant')
        text=' '.join(str(c[k]) for k in keys)+f' {c["level"]&65535} {c["flag39"]} '+c['record'].hex()+' '+c['table'].hex()
        text+=' '+b''.join(struct.pack('>h',v) for v in c['thresholds']).hex()+' '+str(len(c['children']))
        text+=''.join(f' {i} '+b.hex() for i,b in sorted(c['children'].items()));inputs.append(text)
        if len(inputs)==16:flush()
    flush()
    import unicorn
    return {'schema':1,'source_sha256':ALL_SOURCES,'unicorn_version':unicorn.__version__,'cases':count,
            'rng_draws':draws,'zero_path_cases':zero,'executed_followups':calls,'result_sha256':digest.hexdigest(),
            'scope':'Original supplied-allocation factory with original CODE 7 follow-up executed; authored templates/children/metadata, allocator/child creation excluded'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} finalized factory cases, {report["executed_followups"]} executed callbacks and {report["rng_draws"]} draws')


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Original factory variant 7 mode gate and actual long multiply, with follow-up."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_finalized_template_factory import ALL_SOURCES,FollowupExecution
from verify_record_template_factory import original
from verify_record_factory_tail import BASE,CELL
from verify_grid_selector import A5
from verify_rng_cpu import manifest_inputs
from unicorn.m68k_const import UC_M68K_REG_A7


def cases():
    rng=random.Random(2408)
    def make(variant,mode,word,bits,profile,index):
        table=bytearray(rng.randrange(256) for _ in range(76*112));kind=72 if profile==1 else 7
        for i in range(76):
            p=i*112;struct.pack_into('>H',table,p,kind);table[p+20]=(table[p+20]&223)|(32 if profile!=2 else 0)
            table[p+51]=2;struct.pack_into('>II',table,p+60,0x110000,0x110100)
            table[p+2]=[0,127,255][index%3];table[p+8]=[255,127,0][index%3]
            struct.pack_into('>H',table,p+14,word);struct.pack_into('>I',table,p+4,bits)
        children={}
        for i in range(2):
            child=bytearray(32);child[1]=42+i;child[18]=1;struct.pack_into('>H',child,16,2+i*3);children[0x110000+i*0x100]=bytes(child)
        return {'mode':profile,'seed':42+index,'fallback':42,'last':123,'global':[0,128,255][profile],
                'warmup':32 if profile==0 else 0,'record':bytes([0xa5])*112,'variant':variant,'level':-3 if index%2 else 3,
                'flag39':0,'table':bytes(table),'children':children,'thresholds':[-1]*256,'mode_word':mode}
    index=0
    for mode in (-32768,-1,0,1,2,3,4,32767):
        for word in (0,1,32767,32768,65535):
            for bits in (0,1,0x7fffffff,0x80000000,0xffffffff):
                for profile in range(3):
                    yield make(7,mode,word,bits,profile,index);index+=1
        for variant in (65,79):
            for profile in range(3):yield make(variant,mode,65535,0xffffffff,profile,index);index+=1


class ModeExecution(FollowupExecution):
    def __init__(self,sources,c):super().__init__(sources,c);self.multiplies=0
    def prepare(self,uc):
        super().prepare(uc);uc.mem_write(A5-0x9fa,struct.pack('>H',self.c['mode_word']&65535))
    def service(self,uc,address):
        if address==A5+0x42:
            sp=uc.reg_read(UC_M68K_REG_A7);ret,a,b=struct.unpack('>III',bytes(uc.mem_read(sp,12)))
            if ret!=BASE+0x1ae or b!=1250 or a!=struct.unpack('>I',bytes(uc.mem_read(CELL+4,4)))[0]:raise AssertionError('unmodeled variant arithmetic call')
            self.multiplies+=1
        else:super().service(uc,address)
    def inspect(self,uc,observed):
        super().inspect(uc,observed)
        if self.multiplies!=int(self.c['variant']==7 and self.c['mode_word']>2):raise AssertionError(f'mode multiply gate variant={self.c["variant"]} mode={self.c["mode_word"]} got={self.multiplies}')
        if bytes(uc.mem_read(A5-0x9fa,2))!=struct.pack('>H',self.c['mode_word']&65535):raise AssertionError('mode global changed')


def verify(manifest,driver):
    sources={r['id']:d for r,d in manifest_inputs(manifest,'CODE') if r['id'] in ALL_SOURCES}
    if set(sources)!=set(ALL_SOURCES) or any(hashlib.sha256(sources[s]).hexdigest()!=h for s,h in ALL_SOURCES.items()):raise ValueError('unsupported CODE')
    inputs=[];wanted=[];count=0;draws=0;callbacks=0;multiplies=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:raise AssertionError(f'mode variant mismatch {count-len(wanted)+i}')
        inputs.clear();wanted.clear()
    for c in cases():
        execution=ModeExecution(sources,c);line,z,n,f=original(sources,c,followup=execution)
        wanted.append(line);count+=1;draws+=n;callbacks+=f;multiplies+=execution.multiplies;digest.update((line+'\n').encode())
        keys=('mode','seed','fallback','last','global','warmup','variant')
        text=' '.join(str(c[k]) for k in keys)+f' {c["level"]&65535} {c["flag39"]} {c["mode_word"]&65535} '+c['record'].hex()+' '+c['table'].hex()
        text+=' '+b''.join(struct.pack('>h',v) for v in c['thresholds']).hex()+' '+str(len(c['children']))
        text+=''.join(f' {i} '+b.hex() for i,b in sorted(c['children'].items()));inputs.append(text)
        if len(inputs)==16:flush()
    flush()
    import unicorn
    return {'schema':1,'source_sha256':ALL_SOURCES,'unicorn_version':unicorn.__version__,'cases':count,'rng_draws':draws,
            'executed_followups':callbacks,'variant_multiply_calls':multiplies,'result_sha256':digest.hexdigest(),
            'scope':'Variant 7 signed mode gate through original multiply/tail/follow-up, plus unchanged control variants; supplied allocation/templates/children'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} mode cases, {report["variant_multiply_calls"]} multiplies, {report["executed_followups"]} callbacks and {report["rng_draws"]} draws')


if __name__=='__main__':main()

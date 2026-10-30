#!/usr/bin/env python3
"""Original factory common RNG tail on authored records; not whole record creation."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import PROFILES,manifest_inputs
from verify_grid_selector import call,A5,STACK,STOP
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import (UC_CPU_M68K_M68000,UC_M68K_REG_SR,UC_M68K_REG_A4,
    UC_M68K_REG_A5,UC_M68K_REG_A6,UC_M68K_REG_A7,UC_M68K_REG_D0,UC_M68K_REG_PC)

SOURCES={s:p['sha256'] for s,p in PROFILES.items()}
SOURCES[9]='6212eb2b13c828c35e7593f05d15a439421dca9bdd7d6746c04f24220a96c717'
BASE,CELL,FRAME=0x40000,0xb0000,0x160000


def cases():
    rng=random.Random(2008)
    def make(mode,seed,global_byte,record=None):
        return {'mode':mode,'seed':seed,'fallback':[0,42,65535][seed%3],'last':0x89abcdef,'global':global_byte,'warmup':(seed%5)*32 if mode==0 else 0,
                'record':bytes(rng.randrange(256) for _ in range(112)) if record is None else bytes(record)}
    for seed in range(1024):yield make(0,seed,seed&255)
    for mode in (1,2):
        for value in range(256):yield make(mode,0,value)
    for value in range(256):
        record=bytearray(b'\xa5'*112);record[9]=value;yield make(1,0,255,record)
    for word in (0,1,2,32767,32768,65535):
        for bits in (0,1,3,0x7fffffff,0x80000000,0xfffffffd,0xffffffff):
            for global_byte in (0,1,127,128,255):
                record=bytearray(b'\xff'*112);struct.pack_into('>H',record,14,word);struct.pack_into('>I',record,4,bits)
                yield make(1,0,global_byte,record)


def execute(sources,c,prepare=None,inspect=None,start=0x1298,stop=0x1324,early_stop=None):
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000);uc.mem_map(0x10000,0x180000)
    for s,b in ((1,0x10000),(12,0x20000),(5,0x30000),(9,BASE)):uc.mem_write(b,sources[s])
    allowed={0x42,0x62,0x136a,0x1372,0x68a,0x692}
    for offset,sid,entry in ((0x42,1,396),(0x62,1,548),(0x136a,12,29850),(0x1372,12,29884),(0x68a,5,32110),(0x692,5,32200)):
        uc.mem_write(A5+offset,b'\x4e\xf9'+struct.pack('>I',PROFILES[sid]['base']+entry))
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    uc.mem_write(A5-0x56fe,struct.pack('>I',c['last']));uc.mem_write(A5-0x8da,struct.pack('>H',c['fallback']))
    if c['mode']==0:
        call(uc,5,31998,struct.pack('>I',c['seed']),20000)
        if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('initializer endpoint')
    else:
        uc.mem_write(A5-0x5702,struct.pack('>II',c['seed'],c['last'])+struct.pack('>100I',*([c['mode']-1]*100)))
        uc.mem_write(A5-0xb26,struct.pack('>I',c['fallback']))
    for _ in range(c['warmup']):
        call(uc,5,32110,struct.pack('>H',1),20000)
        if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('warmup endpoint')
    for addr,size in ((A5-0x5702,408),(A5-0xb26,4)):
        uc.mem_write(addr-16,b'\x5a'*16);uc.mem_write(addr+size,b'\x5a'*16)
    global_context=b'\xa5'*8+bytes([c['global']])+b'\xa5'*8;uc.mem_write(A5-0x7f1-8,global_context)
    uc.mem_write(CELL-16,b'\xcc'*16+c['record']+b'\xcc'*16)
    uc.mem_write(FRAME-16,b'\xa5'*32);uc.mem_write(STACK-512,b'\x5a'*16);uc.mem_write(STACK+16,b'\x5a'*16)
    for reg,value in ((UC_M68K_REG_A4,CELL),(UC_M68K_REG_A5,A5),(UC_M68K_REG_A6,FRAME),(UC_M68K_REG_A7,STACK)):uc.reg_write(reg,value)
    if prepare is not None:prepare(uc)
    pending=[];draws=[]
    def service(machine,address,size,user):
        if address-A5 not in allowed:raise AssertionError('unmodeled factory service')
        if address in (A5+0x68a,A5+0x692):
            if pending:raise AssertionError('nested wrapper')
            sp=machine.reg_read(UC_M68K_REG_A7);bound=struct.unpack('>H',bytes(machine.mem_read(sp+4,2)))[0]
            pending.append([bound,int(address==A5+0x692)])
        elif not pending:raise AssertionError('RNG helper outside draw')
    def returned(machine,address,size,user):
        if len(pending)!=1:raise AssertionError('unpaired RNG return')
        draws.append(pending.pop()+[machine.reg_read(UC_M68K_REG_D0)&65535])
    uc.hook_add(UC_HOOK_CODE,service,begin=A5+32,end=A5+6335)
    for offset in (0x12a0,0x12b6,0x12c2,0x12d6,0x12e2,0x12ee,0x12fa,0x130e):uc.hook_add(UC_HOOK_CODE,returned,begin=BASE+offset,end=BASE+offset)
    uc.emu_start(BASE+start,BASE+stop,count=100000)
    endpoints={BASE+stop}
    if early_stop is not None:endpoints.add(BASE+early_stop)
    if pending or uc.reg_read(UC_M68K_REG_PC) not in endpoints:raise AssertionError('tail endpoint/draw balance')
    for reg,value in ((UC_M68K_REG_A4,CELL),(UC_M68K_REG_A5,A5),(UC_M68K_REG_A6,FRAME),(UC_M68K_REG_A7,STACK)):
        if uc.reg_read(reg)!=value:raise AssertionError('tail register/stack')
    after=bytes(uc.mem_read(CELL-16,144))
    if after[:16]!=b'\xcc'*16 or after[-16:]!=b'\xcc'*16:raise AssertionError('record guards')
    if bytes(uc.mem_read(FRAME-16,32))!=b'\xa5'*32 or bytes(uc.mem_read(A5-0x7f1-8,17))!=global_context:raise AssertionError('frame/global changed')
    for addr,size in ((A5-0x5702,408),(A5-0xb26,4),(STACK-496,512)):
        if bytes(uc.mem_read(addr-16,16))!=b'\x5a'*16 or bytes(uc.mem_read(addr+size,16))!=b'\x5a'*16:raise AssertionError('RNG/stack guard')
    state=lambda offset:struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    numbers=[state(-0x56fe),state(-0x5702),state(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400)))]
    zero=int(draws[0][2]==0)
    if len(draws)!=(8 if zero else 1):raise AssertionError('tail draw count')
    line=after[16:-16].hex()+' '+' '.join(map(str,numbers))+f' {zero} {len(draws)}'+''.join(' '+' '.join(map(str,d)) for d in draws)
    if inspect is not None:inspect(uc)
    return line,zero,len(draws)


def verify(manifest,driver):
    sources={r['id']:d for r,d in manifest_inputs(manifest,'CODE') if r['id'] in SOURCES}
    if set(sources)!=set(SOURCES) or any(hashlib.sha256(sources[s]).hexdigest()!=h for s,h in SOURCES.items()):raise ValueError('unsupported CODE source')
    inputs=[];wanted=[];count=0;zero=0;initialized_zero=0;warmup_total=0;draws=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('driver output count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:raise AssertionError(f'tail mismatch probe {count-len(wanted)+i}')
        inputs.clear();wanted.clear()
    for c in cases():
        line,z,n=execute(sources,c);wanted.append(line);zero+=z;initialized_zero+=z if c['mode']==0 else 0;warmup_total+=c['warmup'];draws+=n;count+=1;digest.update((line+'\n').encode())
        inputs.append(' '.join(str(c[k]) for k in ('mode','seed','fallback','last','global','warmup'))+' '+c['record'].hex())
        if len(inputs)==128:flush()
    flush()
    if initialized_zero==0:raise AssertionError('initialized/warmed RNG never covered the zero path')
    import unicorn
    return {'schema':1,'source_sha256':SOURCES,'unicorn_version':unicorn.__version__,'cases':count,
            'zero_path_cases':zero,'initialized_zero_path_cases':initialized_zero,'warmup_draws':warmup_total,'rng_draws':draws,'result_sha256':digest.hexdigest(),
            'scope':'CODE 9 common factory tail 0x1298..0x1324; authored records with initialized or authored RNG; template lookup/callback/allocation excluded'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} factory-tail cases, {report["zero_path_cases"]} zero paths and {report["rng_draws"]} RNG draws')


if __name__=='__main__':main()

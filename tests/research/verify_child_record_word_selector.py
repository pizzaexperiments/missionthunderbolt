#!/usr/bin/env python3
"""Compare a read-only raw-word selector with original CODE9 on authored inputs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_rng_cpu import manifest_inputs
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.m68k_const import (UC_CPU_M68K_M68000, UC_M68K_REG_SR,
    UC_M68K_REG_A4, UC_M68K_REG_A5, UC_M68K_REG_A6, UC_M68K_REG_A7,
    UC_M68K_REG_D0, UC_M68K_REG_D7, UC_M68K_REG_PC)

SHA='6212eb2b13c828c35e7593f05d15a439421dca9bdd7d6746c04f24220a96c717'
BASE,A5,RECORD,TEMPLATES,DESCRIPTORS,FRAME,STACK,STOP=0x40000,0x80000,0xb0000,0xd0000,0xe0000,0x160000,0x170000,0x180000
BRANCHES={0x71dc:'descriptor',0x71f2:'incremented_template',0x7214:'template',0x7222:'own_word'}


def cases():
    for kind in range(256):
        for flags in ((0,0),(2,0),(0,2),(2,2),(255,255),(253,253)):
            yield (kind*127%65536,kind,17,*flags,0x5a5a,256,256)
    for index in range(256):
        # The descriptor branch must not access the absent template table.
        yield (index*251%65536,107,index,255,255,0x1234,0,256)
    for kind in (68,119):
        for index in (0,1,32767,32768,65535):
            for seed in (0,1,(65535-kind*307)&65535):
                yield (seed,kind,index,0,0,0xa5a5,256,0)
    for kind in (0,24,25,255,256,32767,32768,65535):
        for own in (0,1,32767,32768,65535):
            # No table is needed on the plain return path, even for negative types.
            yield (42,kind,65535,0,0,own,0,0)


def original(source,c):
    seed,kind,index,flags24,flags25,own,tcount,dcount=c
    record=bytearray((j*31+17)&255 for j in range(56))
    for p,n in ((0,kind),(8,index),(14,own)):struct.pack_into('>H',record,p,n)
    record[24]=flags24;record[25]=flags25
    templates=bytearray((i*17+j*31)&255 for i in range(tcount) for j in range(56))
    for i in range(tcount):struct.pack_into('>H',templates,i*56+14,(i*307+seed)&65535)
    descriptors=bytearray((i*13+j*29)&255 for i in range(dcount) for j in range(12))
    for i in range(dcount):struct.pack_into('>H',descriptors,i*12+10,(i*127+seed*3)&65535)
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x180000);uc.mem_write(BASE,source)
    global_start=A5-0x6000;globals_=bytearray(b'\xa5'*0x8000)
    struct.pack_into('>I',globals_,A5-0x2626-global_start,TEMPLATES)
    struct.pack_into('>I',globals_,A5-0x1a44-global_start,DESCRIPTORS)
    globals_=bytes(globals_);uc.mem_write(global_start,globals_)
    protected=[]
    for address,data in ((RECORD,record),(TEMPLATES,templates),(DESCRIPTORS,descriptors),(FRAME,b'\xa5'*64)):
        guarded=b'\x5a'*16+bytes(data)+b'\x5a'*16
        uc.mem_write(address-16,guarded);protected.append((address-16,guarded))
    uc.mem_write(STACK-128,b'\x5a'*256)
    uc.mem_write(STACK,struct.pack('>II',STOP,RECORD))
    registers=((UC_M68K_REG_A4,0x12345678),(UC_M68K_REG_A5,A5),(UC_M68K_REG_A6,FRAME),(UC_M68K_REG_D7,0x87654321))
    for reg,value in registers:uc.reg_write(reg,value)
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A7,STACK)
    coverage=Counter()
    def observe(machine,address,size,user):coverage[BRANCHES[address-BASE]]+=1
    def reject_service(machine,address,size,user):raise AssertionError('unexpected selector service')
    for offset in BRANCHES:uc.hook_add(UC_HOOK_CODE,observe,begin=BASE+offset,end=BASE+offset)
    uc.hook_add(UC_HOOK_CODE,reject_service,begin=A5+32,end=A5+6335)
    uc.ctl_flush_tb();uc.emu_start(BASE+0x71b2,STOP,count=1000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4:raise AssertionError('selector endpoint/stack')
    for reg,value in registers:
        if uc.reg_read(reg)!=value:raise AssertionError('selector callee-saved register')
    if bytes(uc.mem_read(STACK+4,4))!=struct.pack('>I',RECORD):raise AssertionError('caller argument changed')
    for address in (STACK-128,STACK+112):
        if bytes(uc.mem_read(address,16))!=b'\x5a'*16:raise AssertionError('stack guard')
    for address,data in protected+[(global_start,globals_),(BASE,source)]:
        if bytes(uc.mem_read(address,len(data)))!=data:raise AssertionError('read-only selector changed input/guards/code/globals')
    if sum(coverage.values())!=1:raise AssertionError('selector branch count')
    return uc.reg_read(UC_M68K_REG_D0)&65535,coverage


def verify(manifest,driver):
    sources=[data for r,data in manifest_inputs(manifest,'CODE') if r['id']==9]
    if len(sources)!=1 or hashlib.sha256(sources[0]).hexdigest()!=SHA:raise ValueError('ambiguous/unsupported CODE9 source')
    inputs=[];expected=[];count=0;coverage=Counter();digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',capture_output=True,text=True,check=True,timeout=30).stdout.splitlines()
        if actual!=expected:
            mismatch=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),min(len(actual),len(expected)))
            raise AssertionError(f'raw-word mismatch case {count-len(expected)+mismatch}')
        inputs.clear();expected.clear()
    for c in cases():
        value,branches=original(sources[0],c);count+=1;coverage.update(branches)
        inputs.append(' '.join(map(str,c)));expected.append(str(value));digest.update((str(value)+'\n').encode())
        if len(inputs)==128:flush()
    flush()
    if set(coverage)!=set(BRANCHES.values()):raise AssertionError('missing selector branch coverage')
    import unicorn
    return {'schema':1,'source_sha256':SHA,'unicorn_version':unicorn.__version__,
            'cases':count,'branches':dict(sorted(coverage.items())),'result_sha256':digest.hexdigest(),
            'scope':'CODE9 0x71b2..0x722c returns low word on authored 56/12-byte tables; all inputs/code/globals and guards immutable; no original item semantics'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original-derived evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} read-only word-selector cases across {len(report["branches"])} branches')


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Supplied-allocation original factory paths over authored template tables."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_record_factory_tail import SOURCES,BASE,CELL,execute
from verify_grid_selector import A5,STACK
from verify_rng_cpu import manifest_inputs
from unicorn import UC_HOOK_CODE
from unicorn.m68k_const import (UC_M68K_REG_A0,UC_M68K_REG_A7,UC_M68K_REG_D6,
    UC_M68K_REG_D7,UC_M68K_REG_PC)

TABLE,DESC=0xd0000,0xe0000
PLAIN=[1,2,3,4,5,10,12,13,14,15,16,19,22,25,27,28,29,32,34,37,41,44,47,50,51,52,53,54,55,56,58,62,63,64,66,68,69,70,71,73,76,77,78,80,81,82,83,84,85]
SPECIAL=[60,67,7,0,18,20,21,23,33,86,88,35,46,79,31,39,65,87,38]
SUPPORTED=sorted(PLAIN+SPECIAL)


def cases():
    rng=random.Random(2108);levels=[-32768,-16385,-3277,-3276,-3,-1,0,1,2,3,3276,3277,16384,32767]
    for variant in SUPPORTED+[89,90,255,256,32767]:
        for level in levels:
            for flag in (0,255):
                index=(variant+level+flag)&65535;mode=index%3
                table=bytearray(rng.randrange(256) for _ in range(76*112))
                for i in range(76):struct.pack_into('>H',table,i*112,(i if flag==0 else (i*7+3)%76))
                yield {'mode':mode,'seed':index,'fallback':42,'last':123,'global':rng.choice([0,127,128,255]),
                       'warmup':32 if mode==0 else 0,'record':bytes([0xa5])*112,'variant':variant,'level':level,
                       'flag39':flag,'table':bytes(table)}


def original(sources,c,followup=None):
    observed={'followup':0};descriptors=b'\0'*(76*12)
    def prepare(uc):
        uc.mem_write(TABLE-16,b'\x5a'*16+c['table']+b'\x5a'*16)
        uc.mem_write(DESC-16,b'\x5a'*16+descriptors+b'\x5a'*16)
        pointers=struct.pack('>II',TABLE,DESC);uc.mem_write(A5-0x1a48,pointers)
        uc.mem_write(A5-0x9e8-8,b'\xa5'*8+bytes([c['flag39']])+b'\xa5'*8)
        uc.reg_write(UC_M68K_REG_D6,c['level']&65535);uc.reg_write(UC_M68K_REG_D7,c['variant'])
        uc.mem_write(STACK-8,struct.pack('>II',1,112))
        uc.reg_write(UC_M68K_REG_A7,STACK-8)
        def copied(machine,address,size,user):
            end=machine.reg_read(UC_M68K_REG_A0)
            if (end-TABLE)%112:raise AssertionError('unaligned template copy')
            observed['selected']=(end-TABLE)//112-1
        def at_followup(machine,address,size,user):
            observed['followup']=1
            if followup is None:machine.emu_stop()
        uc.hook_add(UC_HOOK_CODE,copied,begin=BASE+0xe8,end=BASE+0xe8)
        uc.hook_add(UC_HOOK_CODE,at_followup,begin=BASE+0x1334,end=BASE+0x1334)
        if followup is not None:followup.prepare(uc)
    def inspect(uc):
        if 'selected' not in observed:raise AssertionError('template copy not observed')
        if bytes(uc.mem_read(TABLE-16,len(c['table'])+32))!=b'\x5a'*16+c['table']+b'\x5a'*16:raise AssertionError('templates changed')
        if bytes(uc.mem_read(DESC-16,len(descriptors)+32))!=b'\x5a'*16+descriptors+b'\x5a'*16:raise AssertionError('descriptors changed')
        if bytes(uc.mem_read(A5-0x1a48,8))!=struct.pack('>II',TABLE,DESC):raise AssertionError('table pointers changed')
        if bytes(uc.mem_read(A5-0x9e8-8,17))!=b'\xa5'*8+bytes([c['flag39']])+b'\xa5'*8:raise AssertionError('type flag context changed')
        if (uc.reg_read(UC_M68K_REG_D6)&65535)!=(c['level']&65535) or uc.reg_read(UC_M68K_REG_D7)!=c['variant']:raise AssertionError('factory word registers changed')
        if uc.reg_read(UC_M68K_REG_PC)!=BASE+(0x1334 if observed['followup'] and followup is None else 0x133c):raise AssertionError('callback boundary endpoint')
        if followup is not None:followup.inspect(uc,observed)
    line,z,n=execute(sources,c,prepare=prepare,inspect=inspect,start=0xbc,stop=0x133c,early_stop=0x1334 if followup is None else None,service_observer=followup.service if followup is not None else None,prefix_bound=4 if c["variant"]==60 else 10 if c["variant"]==67 else None)
    return line+f' {observed["selected"]} {observed["followup"]}',z,n,observed['followup']


def copy_sweep(sources,driver):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_SR,UC_M68K_REG_A4,UC_M68K_REG_A5,UC_M68K_REG_A6
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000);uc.mem_map(0x10000,0x180000)
    uc.mem_write(BASE,sources[9]);uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    table=bytes((i*17+j*31)&255 for i in range(76) for j in range(112))
    uc.mem_write(TABLE-16,b'\x5a'*16+table+b'\x5a'*16);uc.mem_write(A5-0x1a48,struct.pack('>I',TABLE))
    inputs=[];wanted=[];digest=hashlib.sha256()
    def flush():
        actual=subprocess.run([str(driver.resolve()),'--copy'],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if actual!=wanted:raise AssertionError('template copy sweep mismatch')
        inputs.clear();wanted.clear()
    for variant in range(32768):
        uc.mem_write(CELL-16,b'\xcc'*16+b'\xa5'*112+b'\xcc'*16)
        uc.reg_write(UC_M68K_REG_A4,CELL);uc.reg_write(UC_M68K_REG_A6,0x160000);uc.reg_write(UC_M68K_REG_D7,variant)
        uc.mem_write(STACK-8,struct.pack('>II',1,112));uc.reg_write(UC_M68K_REG_A7,STACK-8)
        uc.emu_start(BASE+0xbc,BASE+0xe8,count=200)
        if uc.reg_read(UC_M68K_REG_PC)!=BASE+0xe8 or uc.reg_read(UC_M68K_REG_A7)!=STACK:raise AssertionError('copy endpoint/stack')
        if uc.reg_read(UC_M68K_REG_A4)!=CELL or uc.reg_read(UC_M68K_REG_A5)!=A5 or uc.reg_read(UC_M68K_REG_A6)!=0x160000:raise AssertionError('copy context')
        record=bytes(uc.mem_read(CELL-16,144))
        if record[:16]!=b'\xcc'*16 or record[-16:]!=b'\xcc'*16:raise AssertionError('copy guards')
        if bytes(uc.mem_read(TABLE-16,len(table)+32))!=b'\x5a'*16+table+b'\x5a'*16:raise AssertionError('copy source changed')
        end=uc.reg_read(UC_M68K_REG_A0)
        if (end-TABLE)%112:raise AssertionError('copy source alignment')
        index=(end-TABLE)//112-1;line=f'{index} '+record[16:-16].hex()
        inputs.append(str(variant));wanted.append(line);digest.update((line+'\n').encode())
        if len(inputs)==512:flush()
    return digest.hexdigest()


def verify(manifest,driver):
    sources={r['id']:d for r,d in manifest_inputs(manifest,'CODE') if r['id'] in SOURCES}
    if set(sources)!=set(SOURCES) or any(hashlib.sha256(sources[s]).hexdigest()!=h for s,h in SOURCES.items()):raise ValueError('unsupported source')
    copy_hash=copy_sweep(sources,driver)
    actual_supported=subprocess.check_output([str(driver.resolve()),'--supported'],text=True)
    if list(map(int,actual_supported.split()))!=SUPPORTED:raise AssertionError('supported variant set')
    inputs=[];wanted=[];count=0;draws=0;zero=0;followups=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native output count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:
                aa,bb=a.split(),b.split();token=next((j for j,(x,y) in enumerate(zip(aa,bb)) if x!=y),min(len(aa),len(bb)))
                raise AssertionError(f'factory mismatch case {count-len(wanted)+i}, token {token}')
        inputs.clear();wanted.clear()
    for c in cases():
        line,z,n,f=original(sources,c);wanted.append(line);count+=1;zero+=z;draws+=n;followups+=f;digest.update((line+'\n').encode())
        keys=('mode','seed','fallback','last','global','warmup','variant')
        inputs.append(' '.join(str(c[k]) for k in keys)+f' {c["level"]&65535} {c["flag39"]} '+c['record'].hex()+' '+c['table'].hex())
        if len(inputs)==16:flush()
    flush()
    import unicorn
    return {'schema':1,'source_sha256':SOURCES,'unicorn_version':unicorn.__version__,'supported_variants_under89':SUPPORTED,
            'copy_probes':32768,'copy_result_sha256':copy_hash,'cases':count,'zero_path_cases':zero,'rng_draws':draws,'followup_boundaries':followups,'result_sha256':digest.hexdigest(),
            'scope':'Supplied allocation, authored templates/descriptors, 65 supported variants under 89 plus nonnegative word fallback variants; stop before final callback; allocator and child creation excluded'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} template-factory cases, {report["rng_draws"]} draws and {report["followup_boundaries"]} callback boundaries')


if __name__=='__main__':main()

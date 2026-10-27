#!/usr/bin/env python3
"""Isolated 68000 RNG-instruction checks. No Mac ROM/OS, game boot or shipped emulator."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from pict_catalog import manifest_inputs

PROFILES={
    1: {'base':0x10000,'sha256':'f04c7611a70c37d04b724cd8862838ca1d97052b91ee94a834d65fcccd6c1102'},
    5: {'base':0x30000,'sha256':'6ca9d6eb7bf1366b60967c4ff339402199584d0147532bffb303d3282af1a466'},
    12:{'base':0x20000,'sha256':'8eb9990abc838f25c1f498107380341236d65339f4506c3357f5f31820092137'},
}
A5=0x50000
STACK=0x78000
STOP=0x88000


def execute(payloads,segment,entry,state_offset,seed):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
    from unicorn.m68k_const import UC_M68K_REG_A5,UC_M68K_REG_A7,UC_M68K_REG_D0,UC_M68K_REG_PC,UC_M68K_REG_SR,UC_CPU_M68K_M68000
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x80000)
    for sid,data in payloads.items():uc.mem_write(PROFILES[sid]['base'],data)
    # Authored loaded-jump stub for the validated A5+0x42 multiply helper.
    uc.mem_write(A5+0x42,b'\x4e\xf9'+struct.pack('>I',PROFILES[1]['base']+396))
    uc.mem_write(A5+state_offset,struct.pack('>I',seed))
    uc.mem_write(STACK,struct.pack('>I',STOP));uc.mem_write(STOP,b'\x4e\x71')
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5);uc.reg_write(UC_M68K_REG_A7,STACK)
    uc.emu_start(PROFILES[segment]['base']+entry,STOP,count=1000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise RuntimeError('routine did not return within instruction limit')
    state=struct.unpack('>I',bytes(uc.mem_read(A5+state_offset,4)))[0]
    return state,uc.reg_read(UC_M68K_REG_D0)&0xffff



def execute_shuffle(payloads,entry,bound,local_seed,selector_seed,table):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
    from unicorn.m68k_const import UC_M68K_REG_A5,UC_M68K_REG_A7,UC_M68K_REG_D0,UC_M68K_REG_PC,UC_M68K_REG_SR,UC_CPU_M68K_M68000
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x80000)
    for sid,data in payloads.items():uc.mem_write(PROFILES[sid]['base'],data)
    for displacement,segment,offset in [(0x42,1,396),(0x62,1,548),(0x136a,12,29850)]:
        uc.mem_write(A5+displacement,b'\x4e\xf9'+struct.pack('>I',PROFILES[segment]['base']+offset))
    uc.mem_write(A5-0x5702,struct.pack('>I',local_seed));uc.mem_write(A5-0xb26,struct.pack('>I',selector_seed))
    uc.mem_write(A5-0x56fa,b''.join(struct.pack('>I',value) for value in table))
    uc.mem_write(STACK,struct.pack('>Ih',STOP,bound));uc.mem_write(STOP,b'\x4e\x71')
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5);uc.reg_write(UC_M68K_REG_A7,STACK)
    uc.emu_start(PROFILES[5]['base']+entry,STOP,count=5000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise RuntimeError('shuffle wrapper did not return')
    return {'result':uc.reg_read(UC_M68K_REG_D0)&0xffffffff,
            'stored_result':struct.unpack('>I',bytes(uc.mem_read(A5-0x56fe,4)))[0],
            'local_seed':struct.unpack('>I',bytes(uc.mem_read(A5-0x5702,4)))[0],
            'selector_seed':struct.unpack('>I',bytes(uc.mem_read(A5-0xb26,4)))[0],
            'table':list(struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400))))}


def verify(manifest,cases,native_driver=None):
    import unicorn
    payloads={}
    for record,data in manifest_inputs(manifest,'CODE'):
        sid=record['id']
        if sid not in PROFILES:continue
        if sid in payloads:raise ValueError('ambiguous CODE IDs')
        if hashlib.sha256(data).hexdigest()!=PROFILES[sid]['sha256']:raise ValueError('unsupported source segment fingerprint')
        payloads[sid]=data
    if set(payloads)!=set(PROFILES):raise ValueError('required source CODE segments missing')
    rng=random.Random(1701)
    seeds=[0,1,42,0x7fffffff,0x80000000,0xffffffff]+[rng.getrandbits(32) for _ in range(cases)]
    observations=[]
    for segment,entry,state_offset in [(12,29850,-0xb26),(5,32072,-0x5702)]:
        for seed in seeds:
            state,output=execute(payloads,segment,entry,state_offset,seed)
            expected=(seed*1103515245+12345)&0xffffffff
            if state!=expected or output!=((expected>>16)&0x7fff):
                raise AssertionError(f'LCG mismatch: CODE {segment}, seed {seed}')
        observations.append({'segment':segment,'entry_offset':entry,'state_a5_displacement':state_offset,
                             'tested_seeds':len(seeds),'instruction_model':'68000 in Unicorn '+unicorn.__version__,
                             'result':'isolated instruction/model match','original_gameplay_verified':False})
    shuffle_count=0
    native_inputs=[];native_expected=[]
    for entry,one_based in [(32110,False),(32200,True)]:
        for bound in [-32768,-1,0,1,2,3,7,100,32767]:
            for local,selector in [(0,0),(1,42),(0xffffffff,0x80000000)]:
                table=[rng.randrange(32768) for _ in range(100)];expected_table=table.copy()
                expected_local,expected_selector=local,selector
                if bound<=0:expected_result=1 if one_based else 0
                else:
                    expected_selector=(selector*1103515245+12345)&0xffffffff
                    slot=((expected_selector>>16)&0x7fff)%100
                    expected_result=table[slot]%bound+(1 if one_based else 0)
                    expected_local=(local*1103515245+12345)&0xffffffff
                    expected_table[slot]=(expected_local>>16)&0x7fff
                actual=execute_shuffle(payloads,entry,bound,local,selector,table)
                expected={'result':expected_result,'stored_result':expected_result,'local_seed':expected_local,
                          'selector_seed':expected_selector,'table':expected_table}
                if actual!=expected:raise AssertionError(f'shuffle model mismatch at entry {entry}, bound {bound}: {actual} vs {expected}')
                native_inputs.append(" ".join(map(str,[int(one_based),bound,local,selector,*table])))
                native_expected.append([actual["result"],actual["stored_result"],actual["local_seed"],actual["selector_seed"],*actual["table"]])
                shuffle_count+=1
    if native_driver:
        run=subprocess.run([str(native_driver.resolve())],input="\n".join(native_inputs)+"\n",text=True,capture_output=True,check=True,timeout=30)
        rows=[[int(value) for value in line.split()] for line in run.stdout.splitlines()]
        if rows!=native_expected:raise AssertionError('native C++ model disagrees with isolated original instructions')
    return {'native_cpp_cases':shuffle_count if native_driver else 0,'schema':1,'supported_source_sha256':{str(k):v['sha256'] for k,v in PROFILES.items()},
            'analytical_memory_addresses_not_runtime_addresses':True,'original_mac_os_present':False,
            'scope':'isolated RNG primitives and bounded shuffled-output wrappers; not initialization or gameplay verification',
            'shuffle_cases':shuffle_count,
            'observations':observations}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--random-cases',type=int,default=64);p.add_argument('--native-driver',type=Path);a=p.parse_args()
    repo=Path(__file__).resolve().parents[2];out=a.output.resolve()
    if out.is_relative_to(repo) and not out.is_relative_to(repo/'local-generated'):p.error('keep research outputs private')
    if out.exists():p.error('refusing to overwrite results')
    if not 0<=a.random_cases<=1024:p.error('random cases must be 0..1024')
    report=verify(a.manifest,a.random_cases,a.native_driver);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Isolated 68000 checks passed: {sum(r["tested_seeds"] for r in report["observations"])} primitive/seed cases plus {report["shuffle_cases"]} shuffled-wrapper cases; no original game booted')

if __name__=='__main__':main()

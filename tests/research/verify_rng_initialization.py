#!/usr/bin/env python3
"""Private 68000 initializer and continued-draw oracle; no original bytes bundled."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import PROFILES,A5,STACK,STOP,manifest_inputs


def machine(payloads):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_SR,UC_M68K_REG_A5
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x80000)
    for sid,data in payloads.items():uc.mem_write(PROFILES[sid]['base'],data)
    for displacement,segment,offset in [(0x42,1,396),(0x62,1,548),(0x136a,12,29850),(0x1372,12,29884)]:
        uc.mem_write(A5+displacement,b'\x4e\xf9'+struct.pack('>I',PROFILES[segment]['base']+offset))
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    uc.mem_write(STOP,b'\x4e\x71')
    return uc


def call(uc,entry,args,limit,segment=5):
    from unicorn.m68k_const import UC_M68K_REG_A7,UC_M68K_REG_PC
    uc.mem_write(STACK,struct.pack('>I',STOP)+args)
    uc.reg_write(UC_M68K_REG_A7,STACK)
    uc.emu_start(PROFILES[segment]['base']+entry,STOP,count=limit)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('instruction limit reached before return')
    if uc.reg_read(UC_M68K_REG_A7)!=STACK+4:raise AssertionError('unexpected stack balance')


def state(uc):
    def word(offset):return struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    return [word(-0x56fe),word(-0x5702),word(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400)))]


def advance(seed):
    seed=(seed*1103515245+12345)&0xffffffff
    return seed,(seed>>16)&32767


def verify(manifest,driver,random_cases):
    payloads={}
    for record,data in manifest_inputs(manifest,'CODE'):
        sid=record['id']
        if sid not in PROFILES:continue
        if sid in payloads or hashlib.sha256(data).hexdigest()!=PROFILES[sid]['sha256']:
            raise ValueError('ambiguous or unsupported source segment')
        payloads[sid]=data
    if set(payloads)!=set(PROFILES):raise ValueError('required source segments missing')
    # The startup caller reads a synthetic low-memory word pair through this
    # accessor before calling initialize(0). This checks the accessor, not OS time.
    accessor_cases=0
    for value in [0,1,42,0x7fffffff,0x80000000,0xffffffff]:
        for pointer in [0,A5-0x8dc]:
            uc=machine(payloads);uc.mem_map(0,0x1000)
            uc.mem_write(0x20c,struct.pack('>I',value))
            call(uc,30160,struct.pack('>I',pointer),1000,segment=12)
            from unicorn.m68k_const import UC_M68K_REG_D0
            if uc.reg_read(UC_M68K_REG_D0)&0xffffffff !=value:raise AssertionError('low-memory accessor return mismatch')
            if pointer and bytes(uc.mem_read(pointer,4))!=struct.pack('>I',value):raise AssertionError('low-memory accessor write mismatch')
            accessor_cases+=1
    rng=random.Random(1702)
    # Zero argument uses fallback; nonzero high-word-only arguments seed with zero.
    cases=[(arg,fallback) for arg in [0,1,42,65535,65536,0x80000000,0xffffffff]
           for fallback in [0,42,65535]]
    cases += [(rng.getrandbits(32),rng.randrange(65536)) for _ in range(random_cases)]
    inputs=[];expected_rows=[];draws=0
    bounds=[-32768,-1,0,1,2,3,7,100,32767]
    for argument,fallback in cases:
        uc=machine(payloads);previous=rng.getrandbits(32)
        uc.mem_write(A5-0x56fe,struct.pack('>I',previous))
        uc.mem_write(A5-0x8da,struct.pack('>H',fallback))
        # Poison prior states/table to prove the initializer replaces them.
        uc.mem_write(A5-0x5702,b'\xff'*4);uc.mem_write(A5-0xb26,b'\xff'*4)
        uc.mem_write(A5-0x56fa,b'\xff'*400)
        call(uc,31998,struct.pack('>I',argument),20000)
        local=1;selector=(argument&65535) if argument else fallback;table=[]
        for _ in range(100):local,value=advance(local);table.append(value)
        expected=[previous,local,selector,*table]
        if state(uc)!=expected:raise AssertionError(f'initializer mismatch for argument {argument}, fallback {fallback}')
        expected_rows.append(expected)
        commands=[]
        for step in range(64):
            one=step%2;bound=bounds[step%len(bounds)] if step<18 else rng.randrange(1,32768)
            commands.extend([one,bound]);before=expected
            last,local,selector,*table=before
            if bound<=0:last=one
            else:
                selector,slot=advance(selector);slot%=100
                last=table[slot]%bound+one
                local,table[slot]=advance(local)
            expected=[last,local,selector,*table]
            call(uc,32200 if one else 32110,struct.pack('>h',bound),5000)
            if state(uc)!=expected:raise AssertionError('continued original-instruction state mismatch')
            from unicorn.m68k_const import UC_M68K_REG_D0
            if uc.reg_read(UC_M68K_REG_D0)&0xffffffff !=last:raise AssertionError('return value mismatch')
            expected_rows.append(expected);draws+=1
        inputs.append(' '.join(map(str,[argument,fallback,previous,64,*commands])))
    result=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,
                          capture_output=True,check=True,timeout=30)
    actual_rows=[[int(value) for value in line.split()] for line in result.stdout.splitlines()]
    if actual_rows!=expected_rows:raise AssertionError('native initialized/continued state differs from original instructions')
    import unicorn
    return {'schema':1,'unicorn':unicorn.__version__,'cpu':'68000',
            'source_sha256':{str(k):v['sha256'] for k,v in PROFILES.items()},
            'low_memory_accessor_cases':accessor_cases,'initializer_cases':len(cases),'continued_draw_cases':draws,
            'native_cpp_state_comparisons':len(expected_rows),
            'scope':'initializer and continued RNG draws with synthetic seed/fallback inputs',
            'original_mac_os_present':False,'original_gameplay_verified':False,
            'fallback_source_meaning':'startup caller copies long at low-memory 0x20c to A5-0x8dc; OS meaning not verified'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--random-cases',type=int,default=16);a=p.parse_args()
    repo=Path(__file__).resolve().parents[2];out=a.output.resolve()
    if out.is_relative_to(repo) and not out.is_relative_to(repo/'local-generated'):p.error('keep results private')
    if out.exists():p.error('refusing to overwrite results')
    if not 0<=a.random_cases<=128:p.error('random cases must be 0..128')
    report=verify(a.manifest,a.native_driver,a.random_cases)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Passed {report["initializer_cases"]} initializers and {report["continued_draw_cases"]} continued draws; '
          f'{report["native_cpp_state_comparisons"]} complete native/68000 state comparisons; no game booted')

if __name__=='__main__':main()

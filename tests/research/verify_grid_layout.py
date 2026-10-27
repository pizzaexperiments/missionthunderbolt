#!/usr/bin/env python3
"""Isolated original grid-pointer builder with a synthetic allocation shim; no game boot."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_rng_cpu import PROFILES,manifest_inputs

A5=0x80000
STACK=0xf0000
STOP=0xf8000


def execute(payloads,base,level,mode):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_A5,UC_M68K_REG_A7,UC_M68K_REG_SR,UC_M68K_REG_D0,UC_M68K_REG_PC
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0xf0000)
    for sid,data in payloads.items():uc.mem_write(PROFILES[sid]['base'],data)
    uc.mem_write(A5+0x42,b'\x4e\xf9'+struct.pack('>I',PROFILES[1]['base']+396))
    uc.mem_write(A5+0xa9a,b'\x4e\x75')  # Authored RTS allocation shim, not recovered allocator behavior.
    uc.mem_write(A5-0x1a40+4*level,struct.pack('>I',base))
    pointers=[];requests=[]
    for row in range(19):
        present=mode=='reuse' or (mode=='mixed' and row%2==0) or (mode=='one-missing' and row!=9)
        pointer=0x90000+row*0x200 if present else 0
        pointers.append(pointer)
        uc.mem_write(A5-0x6a6+4*row,struct.pack('>I',pointer))
        uc.mem_write(0x90000+row*0x200,b'\xa5'*0x200)
        uc.mem_write(0xa0000+row*0x200,b'\xa5'*0x200)
    def allocator(machine,address,size,user_data):
        if address!=A5+0xa9a:return
        stack=machine.reg_read(UC_M68K_REG_A7)
        request=struct.unpack('>II',bytes(machine.mem_read(stack+4,8)))
        if request!=(1,268):raise AssertionError(f'unexpected allocation arguments {request}')
        result=0xa0000+len(requests)*0x200;requests.append(request)
        machine.reg_write(UC_M68K_REG_D0,result)
    uc.hook_add(UC_HOOK_CODE,allocator,begin=A5+0xa9a,end=A5+0xa9a)
    uc.mem_write(STACK,struct.pack('>Ih',STOP,level));uc.mem_write(STOP,b'\x4e\x71')
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5);uc.reg_write(UC_M68K_REG_A7,STACK)
    uc.emu_start(PROFILES[12]['base']+19476,STOP,count=100000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4:
        raise AssertionError('builder did not return with expected stack balance')
    allocated=0;cells=[]
    for row,previous in enumerate(pointers):
        pointer=struct.unpack('>I',bytes(uc.mem_read(A5-0x6a6+4*row,4)))[0]
        expected_pointer=previous or (0xa0000+allocated*0x200)
        if not previous:allocated+=1
        if pointer!=expected_pointer:raise AssertionError('row table reuse/allocation mismatch')
        cells.extend(struct.unpack('>67I',bytes(uc.mem_read(pointer,268))))
        if bytes(uc.mem_read(pointer+268,0x200-268))!=b'\xa5'*(0x200-268):
            raise AssertionError('write beyond row pointer table')
    if len(requests)!=allocated:raise AssertionError('allocation count mismatch')
    expected=[(base+104+row*1340+column*20)&0xffffffff for row in range(19) for column in range(67)]
    if cells!=expected:raise AssertionError('original pointer builder differs from layout hypothesis')
    return cells,allocated


def verify(manifest,driver):
    payloads={}
    for record,data in manifest_inputs(manifest,'CODE'):
        sid=record['id']
        if sid not in (1,12):continue
        if sid in payloads or hashlib.sha256(data).hexdigest()!=PROFILES[sid]['sha256']:
            raise ValueError('ambiguous/unsupported source segment')
        payloads[sid]=data
    if set(payloads)!={1,12}:raise ValueError('required CODE resources missing')
    inputs=[];expected=[];allocations=0
    for base in [0,1,0x40000,0x7fffffc0,0xfffffff0]:
        for level in [-32768,-1,0,1,5,32767]:
            for mode in ['empty','reuse','mixed','one-missing']:
                cells,count=execute(payloads,base,level,mode)
                inputs.append(str(base));expected.append(cells);allocations+=count
    native=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,
                          capture_output=True,check=True,timeout=30)
    actual=[[int(value) for value in row.split()] for row in native.stdout.splitlines()]
    if actual!=expected:raise AssertionError('native address layout disagrees with original instructions')
    import unicorn
    return {'unicorn_version':unicorn.__version__,'cpu':'68000','schema':1,'source_sha256':{str(s):PROFILES[s]['sha256'] for s in (1,12)},
            'routine_segment':12,'routine_offset':19476,'cases':len(expected),
            'cell_address_comparisons':len(expected)*67*19,'synthetic_allocator_calls':allocations,
            'columns':67,'rows':19,'record_bytes':20,'header_bytes':104,
            'base_addresses_are_analytical':True,'original_allocator_executed':False,
            'original_mac_os_present':False,'map_generation_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    repo=Path(__file__).resolve().parents[2];out=a.output.resolve()
    if out.is_relative_to(repo) and not out.is_relative_to(repo/'local-generated'):p.error('keep research outputs private')
    if out.exists():p.error('refusing to overwrite results')
    report=verify(a.manifest,a.native_driver);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Passed {report["cases"]} grid-builder cases and {report["cell_address_comparisons"]} native/original cell-address comparisons; allocation is synthetic')

if __name__=='__main__':main()

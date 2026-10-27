#!/usr/bin/env python3
"""Exhaustive release-prefix wrapper check; observe/skip the final DisposePtr trap."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_rng_cpu import manifest_inputs

SOURCE_SHA='a4b03764578a4d99ec8758315c15ddc2737bb454c939cc9fc0ef3695624250ca'
BASE, STACK, STOP, PAYLOAD = 0x40000, 0xf0000, 0xf8000, 0xb0002


def verify(manifest, driver):
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
    from unicorn.m68k_const import UC_CPU_M68K_M68000, UC_M68K_REG_A0, UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_PC, UC_M68K_REG_SR
    sources=[data for rec,data in manifest_inputs(manifest,'CODE') if rec['id']==11]
    if len(sources)!=1 or hashlib.sha256(sources[0]).hexdigest()!=SOURCE_SHA:
        raise ValueError('missing, ambiguous or unsupported CODE 11')
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x100000);uc.mem_write(BASE,sources[0])
    if bytes(uc.mem_read(BASE+470,2))!=struct.pack('>H',0xa01f):raise ValueError('unexpected disposal trap')
    calls=[]
    def trap(machine,address,size,user):
        calls.append(machine.reg_read(UC_M68K_REG_A0))
        machine.reg_write(UC_M68K_REG_PC,BASE+472)
    uc.hook_add(UC_HOOK_CODE,trap,begin=BASE+470,end=BASE+470)
    inputs=[];wanted=[];trap_count=0
    for pointer in (0,PAYLOAD):
        for word in range(65536):
            raw=struct.pack('>H',word)+b'\x5a'*64;uc.mem_write(PAYLOAD-2,raw)
            uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A7,STACK)
            uc.reg_write(UC_M68K_REG_A6,0x12340000)
            uc.mem_write(STACK,struct.pack('>II',STOP,pointer));calls.clear()
            uc.emu_start(BASE+454,STOP,count=100)
            if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4 or uc.reg_read(UC_M68K_REG_A6)!=0x12340000:
                raise AssertionError('wrapper stack/callee return mismatch')
            after=bytes(uc.mem_read(PAYLOAD-2,len(raw)))
            if after[2:]!=raw[2:]:raise AssertionError('wrapper changed payload or guard')
            if len(calls)>1:raise AssertionError('multiple disposal traps')
            inputs.append(f'{pointer} {word}')
            wanted.append(f'{struct.unpack_from(">H",after)[0]} {len(calls)} {calls[0] if calls else 0}')
            trap_count+=len(calls)
    run=subprocess.run([str(driver.resolve()),'--prefix'],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
    if run.stdout.splitlines()!=wanted:raise AssertionError('native prefix wrapper mismatch')
    import unicorn
    return {'schema':1,'source_sha256':SOURCE_SHA,'segment':11,'entry':454,'unicorn_version':unicorn.__version__,
            'comparisons':len(wanted),'observed_dispose_traps':trap_count,
            'scope':'Original wrapper instructions; DisposePtr trap observed/skipped, not executed',
            'synthetic_payload_address':PAYLOAD,'memory_manager_behavior_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):
        p.error('original-derived evidence must remain private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["comparisons"]} prefix probes; {report["observed_dispose_traps"]} observed DisposePtr call')


if __name__=='__main__':main()

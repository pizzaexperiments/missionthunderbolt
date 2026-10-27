#!/usr/bin/env python3
"""Private exhaustive coordinate and selector-gate instruction checks, not collision/gameplay."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_rng_cpu import manifest_inputs

SOURCE_SHA='6f49e28cabe8e5228ca7e192926133e934e131010932f0d7203c91d83d085430'
BASE=0x30000
STACK=0xf0000
STOP=0xf8000
CELL=0x40000
ROW=0x41000
COLUMN=ROW+2


def verify(manifest,driver):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_A2,UC_M68K_REG_A7,UC_M68K_REG_SR,UC_M68K_REG_PC
    segments=[data for record,data in manifest_inputs(manifest,'CODE') if record['id']==13]
    if len(segments)!=1 or hashlib.sha256(segments[0]).hexdigest()!=SOURCE_SHA:
        raise ValueError('ambiguous or unsupported CODE 13 source')
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0xf0000);uc.mem_write(BASE,segments[0]);uc.mem_write(STOP,b'\x4e\x71')
    inputs=[];expected=[]
    for row in range(256):
        for column in range(256):
            uc.mem_write(ROW,bytes([row,0xa5,column,0xa5]))
            uc.mem_write(STACK,struct.pack('>III',STOP,ROW,COLUMN))
            uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A7,STACK)
            uc.emu_start(BASE+26098,STOP,count=1000)
            if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4:
                raise AssertionError('coordinate helper failed to return with balanced stack')
            actual=bytes(uc.mem_read(ROW,4));signed_row=row if row<128 else row-256;signed_column=column if column<128 else column-256
            wanted=bytes([max(0,min(18,signed_row)),0xa5,max(0,min(66,signed_column)),0xa5])
            if actual!=wanted:raise AssertionError('coordinate clamp or adjacent-byte corruption mismatch')
            inputs.append(f'{row} {column}');expected.append(f'{actual[0]} {actual[2]}')
    native=subprocess.run([str(driver.resolve()),'--clamp'],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
    if native.stdout.splitlines()!=expected:raise AssertionError('native clamp disagrees with original instructions')
    # Probe the original decision blocks; stop before either accepted/rejected caller continuation.
    observation={}
    def branch(machine,address,size,user_data):
        if address in observation['stops']:
            observation['accepted']=address==observation['stops'][0];machine.emu_stop()
    hook=uc.hook_add(UC_HOOK_CODE,branch,begin=BASE+0x3076,end=BASE+0x3156)
    candidate_inputs=[];candidate_expected=[];probes=0
    blocked={1,2,22,25,28,29,30,34}
    for kind in range(256):
        for field16 in [0,1,0x80000000,0xffffffff]:
            wanted=field16==0 and kind not in blocked
            for entry,accepted,rejected in [(0x3076,0x30a8,0x30ba),(0x3112,0x3146,0x3156)]:
                uc.mem_write(CELL,bytes([kind])+b'\0'*15+struct.pack('>I',field16))
                uc.reg_write(UC_M68K_REG_A2,CELL);uc.reg_write(UC_M68K_REG_A7,STACK);uc.reg_write(UC_M68K_REG_SR,0x2000)
                observation.clear();observation['stops']=(BASE+accepted,BASE+rejected)
                uc.emu_start(BASE+entry,STOP,count=1000)
                if observation.get('accepted')!=wanted:raise AssertionError(f'candidate gate mismatch for kind {kind}, field16 {field16}, entry {entry}')
                probes+=1
            candidate_inputs.append(f'{kind} {field16}');candidate_expected.append(str(int(wanted)))
    uc.hook_del(hook)
    native=subprocess.run([str(driver.resolve()),'--candidate'],input='\n'.join(candidate_inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
    if native.stdout.splitlines()!=candidate_expected:raise AssertionError('native candidate gate disagrees with original instructions')
    import unicorn
    return {'unicorn_version':unicorn.__version__,'cpu':'68000','schema':1,'source_sha256':SOURCE_SHA,'coordinate_routine_offset':26098,
            'coordinate_byte_pairs':len(inputs),'selector_gate_probes':probes,
            'native_candidate_cases':len(candidate_inputs),'selector_routine_offset':12328,
            'coordinate_pointer_domain':'two distinct writable bytes with adjacent sentinels',
            'selector_required_zero_field_offset':16,'blocked_kind_bytes':sorted(blocked),
            'scope':'complete isolated clamp; selector decision blocks only, not complete selector',
            'original_mac_os_present':False,'movement_collision_or_generation_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    repo=Path(__file__).resolve().parents[2];out=a.output.resolve()
    if out.is_relative_to(repo) and not out.is_relative_to(repo/'local-generated'):p.error('keep research outputs private')
    if out.exists():p.error('refusing to overwrite results')
    report=verify(a.manifest,a.native_driver);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Passed {report["coordinate_byte_pairs"]} coordinate byte pairs and {report["selector_gate_probes"]} selector-gate probes; native models match')

if __name__=='__main__':main()

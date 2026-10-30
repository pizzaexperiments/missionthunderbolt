#!/usr/bin/env python3
"""Original CODE 7 factory follow-up selection on authored parent/child records."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import manifest_inputs
from verify_linked_records import call,check_return
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_A5

SHA='43eb181114493dd938496157cf0943d5fb5d152b56086fb684122fe50385e852'
A5,PARENT,TABLE,META=0x80000,0xa0000,0xd0000,0xe0000


def cases():
    rng=random.Random(2208)
    def make(kind,count,flag):
        parent=bytearray(rng.randrange(256) for _ in range(112));struct.pack_into('>H',parent,0,kind);parent[51]=count
        flags=bytearray(rng.randrange(256) for _ in range(76));flags[kind]=(flags[kind]&223)|flag
        children={}
        for i in range(count):
            identity=0x110000+i*0x100;struct.pack_into('>I',parent,60+4*i,identity)
            child=bytearray(rng.randrange(256) for _ in range(32));child[8]=child[9]=child[24]=child[25]=0
            struct.pack_into('>H',child,16,[0,1,2,5,32767,32768,65535][i%7]);children[identity]=child
        return {'parent':parent,'flags':flags,'thresholds':[-1]*256,'children':children}
    for count in range(14):
        for kind in (0,1,72,75):
            for flag in (0,32):yield make(kind,count,flag)
    for field in (8,16,18,24,25):
        for value in range(256):
            for high in ((0,128,255) if field in (8,16) else (0,)):
                for kind in (1,72):
                    c=make(kind,3,32);child=c['children'][0x110100]
                    if field in (8,16):struct.pack_into('>H',child,field,(high<<8)|value)
                    else:child[field]=value
                    yield c
    for byte in range(256):
        for threshold in (-32768,-1,0,1,32767):
            for score in (-32768,-1,0,1,32767):
                c=make(72,2,32);c['parent'][18]=byte;c['thresholds']=[threshold]*256
                child=c['children'][0x110100];child[18]=1;struct.pack_into('>h',child,8,score)
                yield c
    for count in range(1,14):
        c=make(1,count,32)
        for i in range(count):
            child=c['children'][0x110000+i*0x100];struct.pack_into('>H',child,16,5)
        yield c


def author_context(uc,c,parent_address=PARENT):
    uc.mem_write(parent_address-16,b'\xcc'*16+bytes(c['parent'])+b'\xcc'*16)
    templates=bytearray(b'\xa5'*(76*112))
    for i,value in enumerate(c['flags']):templates[i*112+20]=value
    metadata=bytearray(b'\x5a'*(256*56))
    for byte,value in enumerate(c['thresholds']):struct.pack_into('>h',metadata,((byte+128)&255)*56+8,value)
    uc.mem_write(TABLE-16,b'\xcc'*16+bytes(templates)+b'\xcc'*16);uc.mem_write(META-16,b'\xcc'*16+bytes(metadata)+b'\xcc'*16)
    uc.mem_write(A5-0x1a48,struct.pack('>I',TABLE));uc.mem_write(A5-0x2626,struct.pack('>I',META+128*56))
    for identity,child in c['children'].items():uc.mem_write(identity-16,b'\xcc'*16+bytes(child)+b'\xcc'*16)
    return bytes(templates),bytes(metadata)


def check_context(uc,c,templates,metadata):
    if bytes(uc.mem_read(TABLE-16,len(templates)+32))!=b'\xcc'*16+templates+b'\xcc'*16:raise AssertionError('template mutation/guard')
    if bytes(uc.mem_read(META-16,len(metadata)+32))!=b'\xcc'*16+metadata+b'\xcc'*16:raise AssertionError('metadata mutation/guard')
    if bytes(uc.mem_read(A5-0x1a48,4))!=struct.pack('>I',TABLE) or bytes(uc.mem_read(A5-0x2626,4))!=struct.pack('>I',META+128*56):raise AssertionError('context pointer mutation')
    for identity,child in c['children'].items():
        if bytes(uc.mem_read(identity-16,64))!=b'\xcc'*16+bytes(child)+b'\xcc'*16:raise AssertionError('child mutation/guard')


def execute(uc,c):
    templates,metadata=author_context(uc,c);uc.reg_write(UC_M68K_REG_A5,A5)
    call(uc,7,9972,struct.pack('>I',PARENT));check_return(uc)
    check_context(uc,c,templates,metadata)
    result=bytes(uc.mem_read(PARENT-16,144))
    if result[:16]!=b'\xcc'*16 or result[-16:]!=b'\xcc'*16:raise AssertionError('parent guards')
    return result[16:-16].hex()


def native_input(c):
    return bytes(c['parent']).hex()+' '+bytes(c['flags']).hex()+' '+b''.join(struct.pack('>h',v) for v in c['thresholds']).hex()+' '+str(len(c['children']))+''.join(f' {i} '+bytes(b).hex() for i,b in sorted(c['children'].items()))


def verify(manifest,driver):
    codes=[d for r,d in manifest_inputs(manifest,'CODE') if r['id']==7]
    if len(codes)!=1 or hashlib.sha256(codes[0]).hexdigest()!=SHA:raise ValueError('unsupported CODE 7')
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000);uc.mem_map(0x10000,0x180000);uc.mem_write(0x20000,codes[0])
    inputs=[];wanted=[];count=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if actual!=wanted:raise AssertionError(f'follow-up mismatch batch ending {count}')
        inputs.clear();wanted.clear()
    for c in cases():
        result=execute(uc,c);inputs.append(native_input(c));wanted.append(result);digest.update((result+'\n').encode());count+=1
        if len(inputs)==128:flush()
    flush()
    import unicorn
    return {'schema':1,'source_sha256':SHA,'unicorn_version':unicorn.__version__,'cases':count,'result_sha256':digest.hexdigest(),
            'scope':'Original CODE 7 follow-up selection on authored parent/children/templates/threshold metadata; no allocator or gameplay interpretation'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} original follow-up cases')


if __name__=='__main__':main()

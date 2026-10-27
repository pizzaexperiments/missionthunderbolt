#!/usr/bin/env python3
"""Original CODE 1 DATA/ZERO expansion and DREL blocks, with resource/OS calls excluded."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import manifest_inputs

BASE, IMAGE, DATA, ZERO, HANDLE = 0x10000,0x60000,0x90000,0xa0000,0xb0000
HASHES={'CODE':'f04c7611a70c37d04b724cd8862838ca1d97052b91ee94a834d65fcccd6c1102',
        'DATA':'c6d01361387c4d5f6c2a7eb5cfc907b09343a30ec2b35477b4471eaeaf52dc7f',
        'ZERO':'bf8e36f8d85e0c351e7adf87e4c04a97ee81fa09740a77200c28d932d32792f2',
        'DREL':'ea3cf82e2d6d0c06f50594a5271859f37a10dfd5f2399d5be93532ea732b8f4e',
        'CODE0':'a02fd7adac1cd2dfbbbed0fa3249e4a8989e16c7bcda6a65c875adf77beb5f1e'}


def sources(manifest):
    result={}
    for typ in ('CODE','DATA','ZERO','DREL'):
        for rec,data in manifest_inputs(manifest,typ):
            key='CODE0' if typ=='CODE' and rec['id']==0 else typ
            if rec['id']!=(1 if key=='CODE' else 0):continue
            if key in result or hashlib.sha256(data).hexdigest()!=HASHES[key]:raise ValueError('ambiguous or unsupported startup resource')
            result[key]=data
    if set(result)!=set(HASHES):raise ValueError('missing startup resource')
    return result


def machine(code):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_SR
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000);uc.mem_map(0x10000,0x100000)
    uc.mem_write(BASE,code);uc.reg_write(UC_M68K_REG_SR,0x2000)
    return uc


def expand_original(code,data,zero,size):
    from unicorn.m68k_const import UC_M68K_REG_A0,UC_M68K_REG_A1,UC_M68K_REG_A2,UC_M68K_REG_A5,UC_M68K_REG_PC
    uc=machine(code);uc.mem_write(DATA,data+b'\xa5'*16);uc.mem_write(ZERO,zero+b'\xa5'*16)
    uc.mem_write(IMAGE-16,b'\x5a'*16+b'\xcc'*size+b'\x5a'*16)
    for reg,value in [(UC_M68K_REG_A0,DATA),(UC_M68K_REG_A1,IMAGE),(UC_M68K_REG_A2,ZERO),(UC_M68K_REG_A5,IMAGE+size)]:uc.reg_write(reg,value)
    uc.emu_start(BASE+0xd8,BASE+0xec,count=2000000)
    if uc.reg_read(UC_M68K_REG_PC)!=BASE+0xec or uc.reg_read(UC_M68K_REG_A1)!=IMAGE+size:raise AssertionError('startup expansion failed to reach endpoint')
    if bytes(uc.mem_read(IMAGE-16,16))!=b'\x5a'*16 or bytes(uc.mem_read(IMAGE+size,16))!=b'\x5a'*16:raise AssertionError('expansion guard changed')
    if bytes(uc.mem_read(DATA,len(data)))!=data or bytes(uc.mem_read(ZERO,len(zero)))!=zero:raise AssertionError('startup inputs changed')
    return bytes(uc.mem_read(IMAGE,size)),uc.reg_read(UC_M68K_REG_A0)-DATA,uc.reg_read(UC_M68K_REG_A2)-ZERO


def relocate_original(code,image,index,entries,alternate):
    from unicorn.m68k_const import UC_M68K_REG_A0,UC_M68K_REG_A2,UC_M68K_REG_A5,UC_M68K_REG_D0,UC_M68K_REG_PC
    uc=machine(code);uc.mem_write(BASE+4,struct.pack('>I',alternate));uc.mem_write(HANDLE,struct.pack('>I',ZERO))
    uc.mem_write(ZERO,entries+b'\xa5'*16);uc.mem_write(IMAGE-16,b'\x5a'*16+image+b'\x5a'*16)
    for reg,value in [(UC_M68K_REG_A0,HANDLE),(UC_M68K_REG_A2,IMAGE+index),(UC_M68K_REG_A5,IMAGE+index),(UC_M68K_REG_D0,len(entries))]:uc.reg_write(reg,value)
    uc.emu_start(BASE+0x104,BASE+0x120,count=200000)
    if uc.reg_read(UC_M68K_REG_PC)!=BASE+0x120 or uc.reg_read(UC_M68K_REG_A0)!=ZERO+len(entries):raise AssertionError('relocation loop/consumption mismatch')
    if bytes(uc.mem_read(IMAGE-16,16))!=b'\x5a'*16 or bytes(uc.mem_read(IMAGE+len(image),16))!=b'\x5a'*16:raise AssertionError('relocation guard changed')
    if bytes(uc.mem_read(ZERO,len(entries)))!=entries:raise AssertionError('relocations changed')
    return bytes(uc.mem_read(IMAGE,len(image)))


def startup_image(resources,alternate=BASE):
    above,below=struct.unpack_from('>II',resources['CODE0'])
    expanded,used_data,used_zero=expand_original(resources['CODE'],resources['DATA'],resources['ZERO'],below)
    if (used_data,used_zero)!=(len(resources['DATA']),len(resources['ZERO'])):raise AssertionError('unconsumed original startup input')
    image=relocate_original(resources['CODE'],expanded+b'\x5a'*above,below,resources['DREL'],alternate)
    return image,below,above


def initialize_in_context(uc,resources,a5):
    """Run bounded startup blocks in the selector context; supply resource handles."""
    from unicorn.m68k_const import UC_M68K_REG_A0,UC_M68K_REG_A1,UC_M68K_REG_A2,UC_M68K_REG_A5,UC_M68K_REG_D0,UC_M68K_REG_PC
    _,below=struct.unpack_from('>II',resources['CODE0'])
    data,zero,reloc,handle=0x120000,0x130000,0x140000,0x150000
    uc.mem_write(data,resources['DATA']);uc.mem_write(zero,resources['ZERO']);uc.mem_write(reloc,resources['DREL'])
    uc.mem_write(a5-below,b'\xcc'*below)
    for reg,value in [(UC_M68K_REG_A0,data),(UC_M68K_REG_A1,a5-below),(UC_M68K_REG_A2,zero),(UC_M68K_REG_A5,a5)]:uc.reg_write(reg,value)
    uc.emu_start(BASE+0xd8,BASE+0xec,count=2000000)
    if (uc.reg_read(UC_M68K_REG_PC),uc.reg_read(UC_M68K_REG_A0),uc.reg_read(UC_M68K_REG_A2))!=(BASE+0xec,data+len(resources['DATA']),zero+len(resources['ZERO'])):
        raise AssertionError('in-context expansion failed')
    uc.mem_write(BASE+4,struct.pack('>I',BASE));uc.mem_write(handle,struct.pack('>I',reloc))
    for reg,value in [(UC_M68K_REG_A0,handle),(UC_M68K_REG_A2,a5),(UC_M68K_REG_D0,len(resources['DREL']))]:uc.reg_write(reg,value)
    uc.emu_start(BASE+0x104,BASE+0x120,count=200000)
    if uc.reg_read(UC_M68K_REG_PC)!=BASE+0x120 or uc.reg_read(UC_M68K_REG_A0)!=reloc+len(resources['DREL']):
        raise AssertionError('in-context relocation failed')


def verify(manifest,driver):
    r=sources(manifest);above,below=struct.unpack_from('>II',r['CODE0']);rng=random.Random(1707)
    fixtures=[(b'\x12\x34',b'',0),(b'\0\0',b'\0\0',2),(b'\0\0',b'\xff\xfe',65536)]
    for _ in range(64):
        data=bytearray();zero=bytearray();size=0
        for i in range(rng.randrange(1,33)):
            value=rng.choice([0,0,0,1,65535,rng.randrange(1,65536)]);data.extend(struct.pack('>H',value));size+=2
            if value==0:
                count=rng.choice([0,2,4,16,254,512]);zero.extend(struct.pack('>H',count));size+=count
        fixtures.append((bytes(data)+b'\xde\xad',bytes(zero)+b'\xa5\xa5',size))
    fixtures.append((r['DATA'],r['ZERO'],below))
    inputs=[];wanted=[]
    for data,zero,size in fixtures:
        image,di,zi=expand_original(r['CODE'],data,zero,size)
        inputs.append(f'{size} {data.hex() or "-"} {zero.hex() or "-"}');wanted.append(f'{di} {zi} {image.hex() or "-"}')
    out=subprocess.run([str(driver.resolve()),'--expand'],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
    if out.stdout.splitlines()!=wanted:raise AssertionError('native expansion mismatch')
    relocations=[]
    for i in range(128):
        size=rng.choice([128,256]);index=size//2;image=bytes(rng.randrange(256) for _ in range(size));entries=bytearray()
        for _ in range(i%17):
            offset=rng.randrange(0,size-3,2)-index;entries.extend(struct.pack('>H',(offset&65535)|rng.randrange(2)))
        relocations.append((image,index,bytes(entries),[0,1,0x80000000,0xffffffff,BASE][i%5]))
    initial,di,zi=expand_original(r['CODE'],r['DATA'],r['ZERO'],below)
    for alternate in (0,1,0x80000000,0xffffffff,BASE):relocations.append((initial+b'\x5a'*above,below,r['DREL'],alternate))
    inputs=[];wanted=[]
    for image,index,entries,alternate in relocations:
        expected=relocate_original(r['CODE'],image,index,entries,alternate)
        inputs.append(f'{index} {IMAGE+index} {alternate} {image.hex()} {entries.hex() or "-"}');wanted.append(expected.hex())
    out=subprocess.run([str(driver.resolve()),'--relocate'],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
    if out.stdout.splitlines()!=wanted:raise AssertionError('native relocation mismatch')
    image,_,_=startup_image(r)
    signed=lambda value:value if value<128 else value-256
    directions=[[signed(image[below-2534+i]),signed(image[below-2522+i])] for i in range(1,9)]
    offsets=[(word&65534)-65536 if word&32768 else word&65534 for word in struct.unpack('>'+str(len(r['DREL'])//2)+'H',r['DREL'])]
    overlap=any(offset<=pos<offset+4 for offset in offsets for pos in list(range(-2533,-2525))+list(range(-2521,-2513)))
    if overlap:raise AssertionError('direction bytes affected by relocation')
    import unicorn
    return {'schema':1,'unicorn_version':unicorn.__version__,'source_sha256':HASHES,'expansion_cases':len(fixtures),
            'relocation_cases':len(relocations),'below_a5':below,'above_a5':above,'data_consumed':di,'zero_consumed':zi,
            'drel_entries':len(offsets),'direction_pairs':directions,'relocation_touches_directions':overlap,
            'scope':'Original bounded CODE 1 blocks; resource/OS calls not executed; alternate base is supplied'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original-derived evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["expansion_cases"]} expansion and {report["relocation_cases"]} relocation cases; direction tables recovered')


if __name__=='__main__':main()

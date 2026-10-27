#!/usr/bin/env python3
"""Connected original CODE 12 traversal/CODE 6 base-word checks on authored grids."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import manifest_inputs
from verify_basic_cell_conversion import GLYPHS
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn.m68k_const import (UC_CPU_M68K_M68000,UC_M68K_REG_SR,UC_M68K_REG_A3,
    UC_M68K_REG_A4,UC_M68K_REG_A5,UC_M68K_REG_A6,UC_M68K_REG_A7,UC_M68K_REG_D0,
    UC_M68K_REG_D7,UC_M68K_REG_PC)

HASHES={6:'4bf2738077a379758097db694d33a198f88e0f5ef3a165d9638aa02c609ad6bd',
        12:'8eb9990abc838f25c1f498107380341236d65339f4506c3357f5f31820092137'}
BASE6,BASE12,A5,GRID,MAP,FRAME,STACK,STOP=0x40000,0x20000,0x80000,0x90000,0xc0000,0x160000,0x170000,0x180000
COUNT=19*67


def machine(sources):
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x180000)
    for sid,base in ((6,BASE6),(12,BASE12)):uc.mem_write(base,sources[sid])
    uc.mem_write(A5+0x742,b'\x4e\xf9'+struct.pack('>I',BASE6+9816))
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    return uc


def base_cases():
    rng=random.Random(1808)
    for word in range(-32768,32768):yield word,rng.randrange(256),rng.randrange(256)
    for row in range(256):
        for column in range(256):yield 29,row,column


def run_base(uc,word,row,column):
    args=struct.pack('>HBBBB',word&65535,row,0xa5,column,0x5a)
    uc.mem_write(STACK-32,b'\xcc'*32+struct.pack('>I',STOP)+args+b'\x5a'*16)
    uc.reg_write(UC_M68K_REG_A7,STACK);uc.reg_write(UC_M68K_REG_A6,FRAME);uc.reg_write(UC_M68K_REG_A4,GRID)
    uc.emu_start(BASE6+9816,STOP,count=50)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4:raise AssertionError('base word endpoint/stack')
    if uc.reg_read(UC_M68K_REG_A4)!=GRID or uc.reg_read(UC_M68K_REG_A6)!=FRAME:raise AssertionError('base word saved register')
    if bytes(uc.mem_read(STACK+4,22))!=args+b'\x5a'*16 or bytes(uc.mem_read(STACK-32,16))!=b'\xcc'*16:raise AssertionError('base word argument/stack guard')
    return uc.reg_read(UC_M68K_REG_D0)&65535


def grid_cases():
    rng=random.Random(1809)
    def make(glyphs,level,flags,byte8,tuning,fill):
        records=bytes(rng.randrange(256) for _ in range(COUNT*20)) if fill is None else bytes([fill])*(COUNT*20)
        return {'glyphs':glyphs,'records':records,'level':level,'flags':flags,'byte8':byte8,'tuning':tuning}
    for glyph in GLYPHS:yield make(bytes([glyph])*COUNT,15,0,255,[65535,32768,1],None)
    for level in (-32768,-1,0,14,15,16,27,28,29,30,32766,32767):
        for flags in (0,16,255):
            glyphs=bytes(GLYPHS[(i*17+level)%len(GLYPHS)] for i in range(COUNT))
            yield make(glyphs,level,flags,rng.choice([0,127,128,255]),[rng.randrange(65536) for _ in range(3)],rng.choice([0,255,None]))
    for _ in range(32):
        yield make(bytes(rng.choice(GLYPHS) for _ in range(COUNT)),rng.randrange(-32768,32768),rng.randrange(256),rng.randrange(256),[rng.randrange(65536) for _ in range(3)],None)


def run_grid(uc,c):
    header=bytearray(b'\xa5'*104);header[6]=c['flags'];header[8]=c['byte8']
    for row in range(19):struct.pack_into('>I',header,28+4*row,MAP+row*67)
    uc.mem_write(GRID-16,b'\x5a'*16+bytes(header)+c['records']+b'\x5a'*16)
    uc.mem_write(MAP-16,b'\x5a'*16+c['glyphs']+b'\x5a'*16)
    frame=bytearray(b'\xa5'*32);uc.mem_write(FRAME-16,bytes(frame))
    uc.mem_write(A5-0x1c60,struct.pack('>3H',*c['tuning']))
    for reg,value in ((UC_M68K_REG_A3,GRID),(UC_M68K_REG_A5,A5),(UC_M68K_REG_A6,FRAME),
                      (UC_M68K_REG_A7,STACK),(UC_M68K_REG_D7,c['level']&65535)):uc.reg_write(reg,value)
    events=[]
    def service(machine,address,size,user):
        if address!=A5+0x742:raise AssertionError('unmodeled grid service')
        sp=machine.reg_read(UC_M68K_REG_A7);args=bytes(machine.mem_read(sp+4,6))
        events.append((args[2],args[4],struct.unpack_from('>H',args)[0]))
    hook=uc.hook_add(UC_HOOK_CODE,service,begin=A5+32,end=A5+6335)
    try:uc.emu_start(BASE12+0x1476,BASE12+0x2b5c,count=400000)
    finally:uc.hook_del(hook)
    if uc.reg_read(UC_M68K_REG_PC)!=BASE12+0x2b5c or uc.reg_read(UC_M68K_REG_A7)!=STACK:raise AssertionError('grid endpoint/stack')
    if events!=[(row,column,(c['level']+1)&65535) for row in range(19) for column in range(67)]:raise AssertionError('grid traversal/call arguments')
    if uc.reg_read(UC_M68K_REG_A4)!=GRID+104+(COUNT-1)*20:raise AssertionError('last cell pointer')
    if uc.reg_read(UC_M68K_REG_D7)&65535!=c['level']&65535:raise AssertionError('caller word changed')
    if uc.reg_read(UC_M68K_REG_A3)!=GRID or uc.reg_read(UC_M68K_REG_A5)!=A5 or uc.reg_read(UC_M68K_REG_A6)!=FRAME:raise AssertionError('grid context register')
    frame[12]=67;frame[13]=19
    if bytes(uc.mem_read(FRAME-16,32))!=bytes(frame):raise AssertionError('grid frame/loop counters')
    if bytes(uc.mem_read(GRID-16,120))!=b'\x5a'*16+bytes(header):raise AssertionError('grid header/prefix guard')
    if bytes(uc.mem_read(GRID+104+COUNT*20,16))!=b'\x5a'*16:raise AssertionError('grid suffix guard')
    if bytes(uc.mem_read(MAP-16,COUNT+32))!=b'\x5a'*16+c['glyphs']+b'\x5a'*16:raise AssertionError('source map/guards')
    if bytes(uc.mem_read(A5-0x1c60,6))!=struct.pack('>3H',*c['tuning']):raise AssertionError('tuning')
    return bytes(uc.mem_read(GRID+104,COUNT*20))


def verify(manifest,driver):
    sources={r['id']:data for r,data in manifest_inputs(manifest,'CODE') if r['id'] in HASHES}
    if set(sources)!=set(HASHES) or any(hashlib.sha256(sources[s]).hexdigest()!=h for s,h in HASHES.items()):raise ValueError('missing/unsupported CODE')
    uc=machine(sources);inputs=[];wanted=[];base_count=0;digest=hashlib.sha256()
    def compare(mode):
        if not inputs:return
        run=subprocess.run([str(driver.resolve()),'--'+mode],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
        actual=run.stdout.splitlines()
        if actual!=wanted:
            first=next((i for i,(a,b) in enumerate(zip(actual,wanted)) if a!=b),None)
            raise AssertionError(f'{mode} mismatch at batch index {first}; outputs {len(actual)} expected {len(wanted)}')
        inputs.clear();wanted.clear()
    for word,row,column in base_cases():
        value=run_base(uc,word,row,column);inputs.append(str(word));wanted.append(str(value));base_count+=1
        digest.update(struct.pack('>H',value))
        if len(inputs)==4096:compare('base')
    compare('base');base_hash=digest.hexdigest();digest=hashlib.sha256();grid_count=0
    for c in grid_cases():
        result=run_grid(uc,c)
        inputs.append(f'{c["flags"]} {c["byte8"]} {c["level"]&65535} '+ ' '.join(map(str,c['tuning']))+' '+c['glyphs'].hex()+' '+c['records'].hex())
        wanted.append(result.hex());digest.update(result);grid_count+=1
        if len(inputs)==8:compare('grid')
    if inputs:compare('grid')
    import unicorn
    return {'schema':1,'source_sha256':HASHES,'unicorn_version':unicorn.__version__,
            'base_word_probes':base_count,'grid_cases':grid_count,'converted_cells':grid_count*COUNT,
            'base_result_sha256':base_hash,'grid_result_sha256':digest.hexdigest(),
            'scope':'Connected CODE 12 outer traversal, CODE 6 seed helper and 43 direct branches; authored initial records, no allocation or creation/RNG branches'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["base_word_probes"]} base-word probes and {report["grid_cases"]} grids / {report["converted_cells"]} cells')


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Original basic glyph branches/shared subtype adjustment on authored cell records."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import manifest_inputs

SHA='8eb9990abc838f25c1f498107380341236d65339f4506c3357f5f31820092137'
BASE,A5,GRID,CELL,MAP,FRAME,STACK=0x20000,0x80000,0x90000,0xb0000,0xc0000,0x160000,0x170000
GLYPHS=[32,119,80,112,120,35,38,37,92,195,96,196,39,197,47,198,177,176,200,164,213,166,211,188,217,163,161,162,212,210,172,140,201,190,173,199,185,191,180,123,125,40,41]


def adjustments():
    for kind in range(256):
        for subtype in range(256):
            for flags4,flags5,flags6 in [(0,0,0),(64,0,0),(0,128,0),(0,0,1)]:
                b=bytearray(b'\xa5'*20);b[0]=kind;b[1]=subtype;b[4]=flags4;b[5]=flags5;b[6]=flags6
                yield bytes(b)
    for field in (4,5,6):
        for value in range(256):
            for kind,subtype in [(0,0),(1,2),(2,0),(27,0),(28,0),(128,0),(2,27),(2,28)]:
                b=bytearray(b'\x5a'*20);b[0]=kind;b[1]=subtype;b[4]=b[5]=b[6]=0;b[field]=value
                yield bytes(b)


def conversions():
    rng=random.Random(1709);weights=[0,1,32767,32768,65535]
    for glyph in GLYPHS:
        for field in ('flags','byte8'):
            for value in range(256):
                cell=bytes(rng.randrange(256) for _ in range(20))
                flags=value if field=='flags' else rng.randrange(256);byte8=value if field=='byte8' else rng.randrange(256)
                yield {'glyph':glyph,'flags':flags,'byte8':byte8,'level':rng.choice([0,1,-1]),
                       'tuning':[rng.choice(weights) for _ in range(3)],'cell':cell}
        for level in (-32768,-1,0,1,46,69,32767):
            for flags in (0,16):
                for fill in (0,255,0xa5):
                    yield {'glyph':glyph,'flags':flags,'byte8':255,'level':level,'tuning':[65535,32768,1],'cell':bytes([fill])*20}


def machine(code):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_SR,UC_M68K_REG_A4
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000);uc.mem_map(0x10000,0x180000)
    uc.mem_write(BASE,code);uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A4,CELL)
    def unexpected(machine,address,size,user):raise AssertionError('basic classifier called unmodeled service')
    uc.hook_add(UC_HOOK_CODE,unexpected,begin=A5+32,end=A5+6335)
    return uc


def run_adjust(uc,cell):
    from unicorn.m68k_const import UC_M68K_REG_PC
    uc.mem_write(CELL-16,b'\x5a'*16+cell+b'\x5a'*16)
    uc.emu_start(BASE+0x2af8,BASE+0x2b40,count=100)
    if uc.reg_read(UC_M68K_REG_PC)!=BASE+0x2b40:raise AssertionError('adjustment endpoint')
    after=bytes(uc.mem_read(CELL-16,52))
    if after[:16]!=b'\x5a'*16 or after[36:]!=b'\x5a'*16:raise AssertionError('adjustment guard')
    result=after[16:36]
    if result[:1]!=cell[:1] or result[2:]!=cell[2:]:raise AssertionError('adjustment changed another field')
    return result.hex()


def run_convert(uc,c):
    from unicorn.m68k_const import UC_M68K_REG_A3,UC_M68K_REG_A4,UC_M68K_REG_A5,UC_M68K_REG_A6,UC_M68K_REG_A7,UC_M68K_REG_D7,UC_M68K_REG_PC
    row,column=(c['glyph']%19),(c['byte8']%67)
    header=bytearray(b'\xa5'*104);header[6]=c['flags'];header[8]=c['byte8']
    for r in range(19):struct.pack_into('>I',header,28+r*4,MAP+r*67)
    grid=bytearray(b'\xcc'*1273);grid[row*67+column]=c['glyph']
    uc.mem_write(GRID,bytes(header)+b'\x5a'*16);uc.mem_write(MAP-16,b'\x5a'*16+bytes(grid)+b'\x5a'*16)
    uc.mem_write(CELL-16,b'\x5a'*16+c['cell']+b'\x5a'*16)
    frame=bytearray(b'\xa5'*32);frame[12]=column;frame[13]=row;uc.mem_write(FRAME-16,bytes(frame))
    uc.mem_write(A5-0x1c60,struct.pack('>3H',*c['tuning']))
    for reg,value in [(UC_M68K_REG_A3,GRID),(UC_M68K_REG_A4,CELL),(UC_M68K_REG_A5,A5),(UC_M68K_REG_A6,FRAME),(UC_M68K_REG_A7,STACK-6),(UC_M68K_REG_D7,c['level']&65535)]:uc.reg_write(reg,value)
    # Entry is after the coordinate helper's seed-word store. Its six-byte
    # argument cleanup remains in this original block and must balance.
    uc.emu_start(BASE+0x14b8,BASE+0x2b40,count=500)
    if uc.reg_read(UC_M68K_REG_PC)!=BASE+0x2b40 or uc.reg_read(UC_M68K_REG_A7)!=STACK:raise AssertionError('conversion endpoint/stack')
    if bytes(uc.mem_read(GRID,120))!=bytes(header)+b'\x5a'*16 or bytes(uc.mem_read(MAP-16,1305))!=b'\x5a'*16+bytes(grid)+b'\x5a'*16:
        raise AssertionError('conversion changed source/header/guards')
    if bytes(uc.mem_read(FRAME-16,32))!=bytes(frame):raise AssertionError('conversion changed frame')
    if bytes(uc.mem_read(A5-0x1c60,6))!=struct.pack('>3H',*c['tuning']):raise AssertionError('tuning changed')
    after=bytes(uc.mem_read(CELL-16,52))
    if after[:16]!=b'\x5a'*16 or after[36:]!=b'\x5a'*16:raise AssertionError('conversion cell guard')
    return after[16:36].hex()


def verify(manifest,driver):
    sources=[data for rec,data in manifest_inputs(manifest,'CODE') if rec['id']==12]
    if len(sources)!=1 or hashlib.sha256(sources[0]).hexdigest()!=SHA:raise ValueError('missing/unsupported CODE 12')
    supported=subprocess.check_output([str(driver.resolve()),'--supported'],text=True)
    if sorted(map(int,supported.split()))!=sorted(GLYPHS):raise AssertionError('native supported-glyph set mismatch')
    uc=machine(sources[0]);inputs=[];wanted=[];hashes={'adjust':hashlib.sha256(),'convert':hashlib.sha256()};counts={'adjust':0,'convert':0}
    def flush(mode):
        if not inputs:return
        run=subprocess.run([str(driver.resolve()),'--'+mode],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
        actual=run.stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native output count mismatch')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:raise AssertionError(f'{mode} mismatch probe {counts[mode]-len(wanted)+i}: {a} != {b}')
        inputs.clear();wanted.clear()
    for cell in adjustments():
        result=run_adjust(uc,cell);inputs.append(cell.hex());wanted.append(result);hashes['adjust'].update((result+'\n').encode());counts['adjust']+=1
        if len(inputs)==4096:flush('adjust')
    flush('adjust')
    for c in conversions():
        result=run_convert(uc,c);inputs.append(f'{c["glyph"]} {c["flags"]} {c["byte8"]} {c["level"]&65535} '+ ' '.join(map(str,c['tuning']))+' '+c['cell'].hex());wanted.append(result)
        hashes['convert'].update((result+'\n').encode());counts['convert']+=1
        if len(inputs)==2048:flush('convert')
    flush('convert')
    import unicorn
    return {'schema':1,'source_sha256':SHA,'segment':12,'unicorn_version':unicorn.__version__,'supported_glyphs':sorted(GLYPHS),
            'adjustment_probes':counts['adjust'],'conversion_probes':counts['convert'],'result_sha256':{k:v.hexdigest() for k,v in hashes.items()},
            'scope':'43 direct-write branches and shared subtype adjustment; no unresolved services, RNG or full record initialization'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["adjustment_probes"]} subtype probes and {report["conversion_probes"]} basic conversion probes')


if __name__=='__main__':main()

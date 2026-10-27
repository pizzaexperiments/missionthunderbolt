#!/usr/bin/env python3
"""Original selector and RNG instructions on synthetic maps; stop before unresolved fallback."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import PROFILES,manifest_inputs

PROFILES={**PROFILES,13:{'base':0x40000,'sha256':'6f49e28cabe8e5228ca7e192926133e934e131010932f0d7203c91d83d085430'}}
A5=0x80000
GRID=0x90000
STACK=0x170000
STOP=0x180000
ROW=0xa0000
COLUMN=ROW+2
SYNTHETIC_DIRECTIONS=[(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]


def call(uc,segment,entry,args,limit):
    from unicorn.m68k_const import UC_M68K_REG_A7
    uc.mem_write(STACK,struct.pack('>I',STOP)+args);uc.reg_write(UC_M68K_REG_A7,STACK)
    uc.emu_start(PROFILES[segment]['base']+entry,STOP,count=limit)


def execute(payloads,seed,fallback,last,directions,cells):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_A5,UC_M68K_REG_A6,UC_M68K_REG_A7,UC_M68K_REG_SR,UC_M68K_REG_D5,UC_M68K_REG_PC
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x180000)
    for sid,data in payloads.items():uc.mem_write(PROFILES[sid]['base'],data)
    for displacement,segment,offset in [(0x42,1,396),(0x62,1,548),(0x136a,12,29850),(0x1372,12,29884),(0x68a,5,32110),(0x692,5,32200)]:
        uc.mem_write(A5+displacement,b'\x4e\xf9'+struct.pack('>I',PROFILES[segment]['base']+offset))
    uc.mem_write(A5-0x56fe,struct.pack('>I',last));uc.mem_write(A5-0x8da,struct.pack('>H',fallback))
    uc.mem_write(STOP,b'\x4e\x71');uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    call(uc,5,31998,struct.pack('>I',seed),20000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('initializer instruction limit')
    for index,(row,column) in enumerate(directions,1):
        uc.mem_write(A5-0x9e6+index,bytes([row&255]));uc.mem_write(A5-0x9da+index,bytes([column&255]))
    raw=bytearray(104+67*19*20)
    for index,(kind,field16) in enumerate(cells):
        raw[104+index*20]=kind;struct.pack_into('>I',raw,104+index*20+16,field16)
    uc.mem_write(GRID,bytes(raw));uc.mem_write(ROW,b'\xa5\x5a\xa5\x5a')
    observed={}
    def stop_point(machine,address,size,user_data):
        if address==PROFILES[13]['base']+0x3d7e:
            observed.update(outcome=2,iterations=(machine.reg_read(UC_M68K_REG_D5)&65535)-1)
            stack=machine.reg_read(UC_M68K_REG_A7)
            _,_,row_pointer,column_pointer=struct.unpack('>IIII',bytes(machine.mem_read(stack,16)))
            observed['row']=machine.mem_read(row_pointer,1)[0];observed['column']=machine.mem_read(column_pointer,1)[0]
            machine.emu_stop()
        else:
            observed['outcome']=0 if address==PROFILES[13]['base']+0x30a8 else 1
            observed['iterations']=machine.reg_read(UC_M68K_REG_D5)&65535
    for offset in [0x30a8,0x3146,0x3d7e]:
        uc.hook_add(UC_HOOK_CODE,stop_point,begin=PROFILES[13]['base']+offset,end=PROFILES[13]['base']+offset)
    call(uc,13,12328,struct.pack('>III',GRID,ROW,COLUMN),2000000)
    if 'outcome' not in observed:raise AssertionError('selector hit instruction limit or unexpected path')
    if observed['outcome']!=2:
        if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4:raise AssertionError('selector did not return with balanced stack')
        observed['row']=uc.mem_read(ROW,1)[0];observed['column']=uc.mem_read(COLUMN,1)[0]
    if bytes(uc.mem_read(GRID,len(raw)))!=bytes(raw):raise AssertionError('pre-fallback selector unexpectedly changed grid records')
    if uc.mem_read(ROW+1,1)[0]!=0x5a or uc.mem_read(COLUMN+1,1)[0]!=0x5a:raise AssertionError('coordinate output overwrote adjacent bytes')
    def state(offset):return struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    return [observed['outcome'],observed['iterations'],observed['row'],observed['column'],
            state(-0x56fe),state(-0x5702),state(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400)))]


def verify(manifest,driver):
    payloads={}
    for record,data in manifest_inputs(manifest,'CODE'):
        sid=record['id']
        if sid not in PROFILES:continue
        if sid in payloads or hashlib.sha256(data).hexdigest()!=PROFILES[sid]['sha256']:raise ValueError('ambiguous or unsupported CODE segment')
        payloads[sid]=data
    if set(payloads)!=set(PROFILES):raise ValueError('required source segments missing')
    inputs=[];expected=[];outcomes=[0,0,0];rng=random.Random(1704)
    for seed in [0,1,42,65536,0xffffffff]:
        for direction_mode in range(3):
            directions=(SYNTHETIC_DIRECTIONS if direction_mode==0 else SYNTHETIC_DIRECTIONS[3:]+SYNTHETIC_DIRECTIONS[:3] if direction_mode==1
                        else [(-128,-128),(127,127),(-128,127),(127,-128),(0,127),(127,0),(0,-128),(-128,0)])
            for pattern in ['empty','blocked','field16-blocked','corner-only','checkerboard','sparse','mixed-kinds']:
                cells=[]
                for y in range(19):
                    for x in range(67):
                        if pattern=='empty':cell=(0,0)
                        elif pattern=='blocked':cell=(1,0)
                        elif pattern=='field16-blocked':cell=(0,0x80000000)
                        elif pattern=='corner-only':cell=(0 if x==0 and y==0 else 1,0)
                        elif pattern=='checkerboard':cell=(1 if (x+y)%2 else 0,0)
                        elif pattern=='sparse':cell=(0 if rng.randrange(20)==0 else 1,0)
                        else:cell=(rng.randrange(256),rng.choice([0,0,0,1]))
                        cells.append(cell)
                last=rng.getrandbits(32);fallback=42
                result=execute(payloads,seed,fallback,last,directions,cells)
                expected.append(result);outcomes[result[0]]+=1
                values=[seed,fallback,last,*[n for d in directions for n in d],*[n for c in cells for n in c]]
                inputs.append(' '.join(map(str,values)))
    native=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
    actual=[[int(v) for v in line.split()] for line in native.stdout.splitlines()]
    if actual!=expected:
        for index,(a,e) in enumerate(zip(actual,expected)):
            if a!=e:raise AssertionError(f'native selector mismatch at synthetic case {index}: {a[:7]} vs {e[:7]}')
        raise AssertionError('native selector case count mismatch')
    import unicorn
    return {'schema':1,'unicorn_version':unicorn.__version__,'cpu':'68000',
            'source_sha256':{str(s):p['sha256'] for s,p in PROFILES.items()},
            'cases':len(expected),'outcomes':dict(zip(['direct','neighbor','needs-fallback'],outcomes)),
            'synthetic_direction_tables':True,'historical_direction_table_contents_verified':False,
            'full_rng_state_compared':True,'fallback_instructions_executed':False,
            'scope':'original selector and RNG until return or unresolved fallback entry',
            'map_generation_or_gameplay_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    repo=Path(__file__).resolve().parents[2];out=a.output.resolve()
    if out.is_relative_to(repo) and not out.is_relative_to(repo/'local-generated'):p.error('keep research outputs private')
    if out.exists():p.error('refusing to overwrite results')
    report=verify(a.manifest,a.native_driver);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Passed {report["cases"]} original-selector/native/RNG cases: {report["outcomes"]}; unresolved fallback was not executed')

if __name__=='__main__':main()

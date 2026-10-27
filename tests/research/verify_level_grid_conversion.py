#!/usr/bin/env python3
"""Connected original traversal, six level glyphs and original RNG on authored maps."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import PROFILES,manifest_inputs
from verify_direct_grid_conversion import (HASHES,A5,GRID,FRAME,STACK,STOP,BASE12,COUNT,machine,run_grid)
from verify_basic_cell_conversion import GLYPHS
from verify_grid_selector import call
from unicorn import UC_HOOK_CODE
from unicorn.m68k_const import UC_M68K_REG_A7,UC_M68K_REG_D0,UC_M68K_REG_PC

EXTRA=[215,175,187,171,94,118]
SOURCES={**HASHES,**{s:PROFILES[s]['sha256'] for s in (1,5)}}


def cases():
    rng=random.Random(1908)
    levels=[-32768,-257,-256,-255,-1,0,1,254,255,256,257,32767]
    def make(glyphs,level,flags,index):
        return {'glyphs':glyphs,'records':bytes(rng.randrange(256) for _ in range(COUNT*20)),
                'level':level,'flags':flags,'byte8':rng.choice([0,127,128,255]),
                'tuning':[rng.choice([0,1,32767,32768,65535]) for _ in range(3)],
                'extra':[rng.choice([0,1,32767,32768,65535]) for _ in range(3)],
                'seed':[0,1,42,65536,0xffffffff][index%5],'fallback':[0,42,65535][index%3],'last':0x89abcdef}
    for glyph in EXTRA:
        for level in levels:
            for flags in (0,16):yield make(bytes([glyph])*COUNT,level,flags,glyph+level+flags)
    for index in range(32):
        yield make(bytes(rng.choice(GLYPHS+EXTRA) for _ in range(COUNT)),rng.choice(levels),rng.randrange(256),index)
    for index,level in enumerate(levels):
        glyphs=bytearray(b' '*COUNT)
        for i,g in zip([0,66,67,COUNT-68,COUNT-67,COUNT-1],EXTRA):glyphs[i]=g
        yield make(bytes(glyphs),level,255,index)


def execute(sources,c):
    uc=machine(sources)
    for sid in (1,5):uc.mem_write(PROFILES[sid]['base'],sources[sid])
    allowed={0x42,0x62,0x136a,0x1372,0x692}
    for offset,sid,entry in [(0x42,1,396),(0x62,1,548),(0x136a,12,29850),(0x1372,12,29884),(0x692,5,32200)]:
        uc.mem_write(A5+offset,b'\x4e\xf9'+struct.pack('>I',PROFILES[sid]['base']+entry))
    uc.mem_write(A5-0x56fe,struct.pack('>I',c['last']));uc.mem_write(A5-0x8da,struct.pack('>H',c['fallback']))
    call(uc,5,31998,struct.pack('>I',c['seed']),20000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('initializer did not return')
    extra_offsets=(-0x1c22,-0x1c20,-0x1c1c)
    for offset,value in zip(extra_offsets,c['extra']):uc.mem_write(A5+offset,struct.pack('>H',value))
    pending=[];draws=[]
    def service(machine,address):
        if address-A5 not in allowed:raise AssertionError('unmodeled level-grid service')
        if address==A5+0x692:
            if pending:raise AssertionError('nested RNG wrapper')
            sp=machine.reg_read(UC_M68K_REG_A7);bound=struct.unpack('>H',bytes(machine.mem_read(sp+4,2)))[0]
            row=machine.mem_read(FRAME-3,1)[0];column=machine.mem_read(FRAME-4,1)[0]
            if c['glyphs'][row*67+column] not in (94,118) or c['level']==0 or bound!=3:raise AssertionError('unexpected RNG draw')
            pending.append([row,column,bound,1])
        elif not pending:raise AssertionError('RNG helper outside observed draw')
    def returned(machine,address,size,user):
        if len(pending)!=1:raise AssertionError('RNG return without entry')
        draws.append(pending.pop()+[machine.reg_read(UC_M68K_REG_D0)&65535])
    hooks=[uc.hook_add(UC_HOOK_CODE,returned,begin=BASE12+offset,end=BASE12+offset) for offset in (0x2618,0x264e)]
    result=run_grid(uc,c,service)
    for hook in hooks:uc.hook_del(hook)
    if pending:raise AssertionError('unfinished RNG draw')
    for offset,value in zip(extra_offsets,c['extra']):
        if bytes(uc.mem_read(A5+offset,2))!=struct.pack('>H',value):raise AssertionError('extra tuning changed')
    if bytes(uc.mem_read(A5-0x8da,2))!=struct.pack('>H',c['fallback']):raise AssertionError('fallback changed')
    state=lambda offset:struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    numbers=[state(-0x56fe),state(-0x5702),state(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400)))]
    line=' '.join(map(str,numbers))+' '+result.hex()+' '+str(len(draws))+''.join(' '+' '.join(map(str,d)) for d in draws)
    return line,len(draws)


def verify(manifest,driver):
    sources={r['id']:data for r,data in manifest_inputs(manifest,'CODE') if r['id'] in SOURCES}
    if set(sources)!=set(SOURCES) or any(hashlib.sha256(sources[s]).hexdigest()!=h for s,h in SOURCES.items()):raise ValueError('missing/unsupported CODE')
    inputs=[];wanted=[];count=0;draws=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        run=subprocess.run([str(driver.resolve()),'--grid'],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
        actual=run.stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native output count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:
                aa,bb=a.split(),b.split();token=next((j for j,(x,y) in enumerate(zip(aa,bb)) if x!=y),min(len(aa),len(bb)))
                raise AssertionError(f'level-grid mismatch case {count-len(wanted)+i}, token {token}')
        inputs.clear();wanted.clear()
    for c in cases():
        line,n=execute(sources,c);wanted.append(line);draws+=n;count+=1;digest.update((line+'\n').encode())
        inputs.append(' '.join(map(str,[c['flags'],c['byte8'],c['level']&65535,*c['tuning'],*c['extra'],c['seed'],c['fallback'],c['last']]))+' '+c['glyphs'].hex()+' '+c['records'].hex())
        if len(inputs)==8:flush()
    flush()
    import unicorn
    return {'schema':1,'source_sha256':SOURCES,'unicorn_version':unicorn.__version__,
            'new_glyphs':EXTRA,'grid_cases':count,'converted_cells':count*COUNT,'rng_draws':draws,
            'result_sha256':digest.hexdigest(),'scope':'Connected conversion for 49 glyphs including six raw level branches; original initializer, helper and RNG, explicit authored initial records'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["grid_cases"]} grids / {report["converted_cells"]} cells and {report["rng_draws"]} RNG draws')


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Original CODE 12 map-byte preparation with original RNG; authored maps only."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_rng_cpu import PROFILES,manifest_inputs
from verify_grid_selector import A5,GRID,STACK,STOP,call

MAP,FRAME,METADATA=0xb0000,0x160000,0xe0000


def cases():
    def make(name,map_bytes,seed=42,flags=0,level=1,metadata=0,fallback=42):
        return {'name':name,'map':map_bytes,'seed':seed,'flags':flags,'level':level,'metadata':metadata,'fallback':fallback,'last':123}
    for value in range(256):yield make(f'uniform-{value}',bytes([value])*1273)
    mixed=bytes(32 if i%2 else [0,46,59,45,36,255][i%6] for i in range(1273))
    for flags in range(256):yield make(f'flags-{flags}',mixed,flags=flags,metadata=(flags*17)&255)
    for metadata in range(256):yield make(f'metadata-{metadata}',b' '*1273,flags=4,metadata=metadata)
    levels=[-32768,-1,0,16,17,45,46,47,68,69,70,32767]
    for level in levels:
        for flags in (0,4):
            for metadata in (0,127,128,255):
                for seed in (0,1,65536,0xffffffff):
                    for mode,map_bytes in enumerate((b' '*1273,mixed)):
                        yield make(f'matrix-{level}-{flags}-{metadata}-{seed}-{mode}',map_bytes,seed,flags,level,metadata)
    rng=random.Random(1708)
    for index in range(64):
        map_bytes=bytes(rng.choice([32,32,32,0,46,59,45,36,255]) for _ in range(1273))
        yield make(f'seeded-{index}',map_bytes,rng.getrandbits(32),rng.randrange(256),rng.choice(levels),rng.randrange(256),rng.choice([0,42,65535]))


def execute(payloads,case):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_SR,UC_M68K_REG_A0,UC_M68K_REG_A3,UC_M68K_REG_A5,UC_M68K_REG_A6,UC_M68K_REG_A7,UC_M68K_REG_D0,UC_M68K_REG_D7,UC_M68K_REG_PC
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000);uc.mem_map(0x10000,0x180000)
    for sid,data in payloads.items():uc.mem_write(PROFILES[sid]['base'],data)
    for displacement,sid,offset in [(0x42,1,396),(0x62,1,548),(0x136a,12,29850),(0x1372,12,29884),(0x68a,5,32110),(0x692,5,32200)]:
        uc.mem_write(A5+displacement,b'\x4e\xf9'+struct.pack('>I',PROFILES[sid]['base']+offset))
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    uc.mem_write(A5-0x56fe,struct.pack('>I',case['last']));uc.mem_write(A5-0x8da,struct.pack('>H',case['fallback']))
    call(uc,5,31998,struct.pack('>I',case['seed']),20000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('initializer failed')
    header=bytearray(b'\xa5'*104);header[6]=case['flags']
    for row in range(19):struct.pack_into('>I',header,28+row*4,MAP+row*67)
    uc.mem_write(GRID,bytes(header)+b'\x5a'*16);uc.mem_write(MAP-16,b'\x5a'*16+case['map']+b'\x5a'*16)
    metadata=bytearray(b'\x5a'*16);metadata[2]=case['metadata'];uc.mem_write(METADATA,bytes(metadata))
    metadata_slot=A5-0x187c+case['level']*4;uc.mem_write(metadata_slot,struct.pack('>I',METADATA))
    uc.mem_write(FRAME-16,b'\xa5'*32);uc.reg_write(UC_M68K_REG_A6,FRAME);uc.reg_write(UC_M68K_REG_A3,GRID)
    uc.reg_write(UC_M68K_REG_D7,case['level']&65535);uc.reg_write(UC_M68K_REG_A7,STACK)
    draws=[];writes=[];attempts=[0,0,0];observed={}
    base=PROFILES[12]['base'];phase_points={base+0x1310:0,base+0x13c6:1,base+0x1426:2}
    returns=[base+p for p in (0x1318,0x1324,0x134a,0x13ce,0x13da,0x1420,0x142e,0x143a)]
    def hook(machine,address,size,user):
        if address in phase_points:
            observed['phase']=phase_points[address];attempts[observed['phase']]+=1
        elif address in (A5+0x68a,A5+0x692):
            sp=machine.reg_read(UC_M68K_REG_A7);bound=struct.unpack('>H',bytes(machine.mem_read(sp+4,2)))[0]
            if 'pending' in observed:raise AssertionError('nested external RNG entry')
            observed['pending']=(bound,int(address==A5+0x692))
        else:
            bound,one=observed.pop('pending');draws.append([bound,one,machine.reg_read(UC_M68K_REG_D0)&65535])
    for point in [*phase_points,A5+0x68a,A5+0x692,*returns]:uc.hook_add(UC_HOOK_CODE,hook,begin=point,end=point)
    def memory_write(machine,access,address,size,value,user):
        if size!=1:raise AssertionError('unexpected glyph write width')
        index=address-MAP;writes.append([observed['phase'],index//67,index%67,machine.mem_read(address,1)[0],value&255])
    uc.hook_add(UC_HOOK_MEM_WRITE,memory_write,begin=MAP,end=MAP+1272)
    uc.emu_start(base+0x1302,base+0x1476,count=1000000)
    if uc.reg_read(UC_M68K_REG_PC)!=base+0x1476 or uc.reg_read(UC_M68K_REG_A7)!=STACK or 'pending' in observed:
        raise AssertionError('stage endpoint/stack/RNG trace mismatch')
    for reg,value in [(UC_M68K_REG_A3,GRID),(UC_M68K_REG_A5,A5),(UC_M68K_REG_A6,FRAME),(UC_M68K_REG_D7,case['level']&65535)]:
        if uc.reg_read(reg)!=value:raise AssertionError('unexpected context register change')
    if bytes(uc.mem_read(GRID,120))!=bytes(header)+b'\x5a'*16 or bytes(uc.mem_read(METADATA,16))!=bytes(metadata):raise AssertionError('header/metadata changed')
    if bytes(uc.mem_read(MAP-16,16))!=b'\x5a'*16 or bytes(uc.mem_read(MAP+1273,16))!=b'\x5a'*16:raise AssertionError('map guard changed')
    frame=bytes(uc.mem_read(FRAME-16,32))
    if frame[:12]!=b'\xa5'*12 or frame[14:]!=b'\xa5'*18:raise AssertionError('unrelated frame bytes changed')
    state=lambda offset:struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    numbers=[*attempts,state(-0x56fe),state(-0x5702),state(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400)))]
    line=' '.join(map(str,numbers))+' '+bytes(uc.mem_read(MAP,1273)).hex()+' '+str(len(draws))
    line+=''.join(' '+' '.join(map(str,d)) for d in draws)+' '+str(len(writes))+''.join(' '+' '.join(map(str,w)) for w in writes)
    return line,{'attempts':attempts,'draws':len(draws),'writes':len(writes),'result_sha256':hashlib.sha256(line.encode()).hexdigest()}


def verify(manifest,driver):
    payloads={}
    for rec,data in manifest_inputs(manifest,'CODE'):
        sid=rec['id']
        if sid not in PROFILES:continue
        if sid in payloads or hashlib.sha256(data).hexdigest()!=PROFILES[sid]['sha256']:raise ValueError('unsupported source segment')
        payloads[sid]=data
    if set(payloads)!=set(PROFILES):raise ValueError('missing source segment')
    inputs=[];wanted=[];summaries=[]
    for case in cases():
        inputs.append(' '.join(str(case[k] if k!='level' else case[k]&65535) for k in ('seed','fallback','last','flags','level','metadata'))+' '+case['map'].hex())
        line,summary=execute(payloads,case);wanted.append(line);summaries.append({'name':case['name'],**summary})
    run=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=60)
    actual=run.stdout.splitlines()
    if len(actual)!=len(wanted):raise AssertionError('native stage result count mismatch')
    for index,(a,b) in enumerate(zip(actual,wanted)):
        if a!=b:
            aa,bb=a.split(),b.split();token=next((i for i,(x,y) in enumerate(zip(aa,bb)) if x!=y),min(len(aa),len(bb)))
            raise AssertionError(f'preparation mismatch {summaries[index]["name"]}, token {token}')
    import unicorn
    return {'schema':1,'unicorn_version':unicorn.__version__,'source_profiles':PROFILES,'segment':12,'start':4866,'stop':5238,
            'scope':'bounded map-byte preparation with original RNG; not whole level generation or glyph semantics',
            'cases':len(wanted),'rng_calls':sum(s['draws'] for s in summaries),'map_writes':sum(s['writes'] for s in summaries),'results':summaries}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original-derived evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} glyph-preparation cases, {report["rng_calls"]} RNG calls, {report["map_writes"]} byte writes')


if __name__=='__main__':main()

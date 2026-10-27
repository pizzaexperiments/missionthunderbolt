#!/usr/bin/env python3
"""Original fallback control flow on synthetic records with explicit linked-record service shims."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import random
import subprocess
from verify_grid_selector import SYNTHETIC_DIRECTIONS,PROFILES,A5,GRID,STACK,STOP,ROW,COLUMN,call,manifest_inputs

PRIMARY=0xb0000
CHILD=0xb1000
LINK12=0xc0000


def record(kind=1,byte8=1,flags4=0,flags5=0,base=0,link12=0,link16=0,byte6=171):
    data=bytearray([kind,base,0x12,0x34,flags4,flags5,byte6,0xcd,byte8,0x55,0x66,0x77]+[0]*8)
    struct.pack_into('>II',data,12,link12,link16)
    return bytes(data)


def cases():
    defaults={'seed':42,'fallback':42,'last':123,'budget':1,'query':1,'word16':1,'byte25':0,'word12':1,'byte51':0,'child_word':1,'child_flags':0}
    def make(name,cell=None,changes=None,**parameters):
        config={**defaults,**parameters};grid=bytearray((cell or record())*1273)
        for row,column,value in changes or []:grid[(row*67+column)*20:(row*67+column+1)*20]=value
        return {'name':name,**config,'grid':bytes(grid)}
    yield make('first-scan',changes=[(2,3,record(0,byte8=0))])
    yield make('scan-order',changes=[(2,1,record(0,byte8=0)),(1,65,record(0,byte8=0))])
    yield make('border-excluded',changes=[(0,0,record(0,byte8=0)),(18,66,record(0,byte8=0))])
    yield make('second-scan-release',changes=[(1,1,record(0,byte8=0,link16=PRIMARY))])
    yield make('second-scan-declined',changes=[(1,1,record(0,byte8=0,link16=PRIMARY))],query=0)
    yield make('second-scan-nonzero-word',changes=[(1,1,record(0,byte8=0,link16=PRIMARY))],query=65535)
    yield make('zero-budget',budget=0)
    for value in range(256):yield make(f'kind-{value}',cell=record(value))
    for value in range(256):
        yield make(f'flags4-{value}',cell=record(2,flags4=value))
        yield make(f'flags5-{value}',cell=record(22,flags5=value))
        yield make(f'combined-flags-{value}',cell=record(35,flags4=value,flags5=value,byte6=value))
    for kind in [0,1,2,22,25,28,29,35,128,255]:
        yield make(f'base51-{kind}',cell=record(kind,base=51))
    for seed in [0,1,65535,65536,0x80000000,0xffffffff]:yield make(f'seed-{seed}',seed=seed)
    for byte25,word16 in [(0,1),(1,1),(128,52),(128,1)]:
        yield make(f'link16-{word16}-{byte25}',cell=record(link16=PRIMARY),byte25=byte25,word16=word16)
    for word12,count,word,flags in [(1,0,1,0),(73,0,1,0),(1,1,52,0),(1,1,1,1),(1,127,1,0),(1,128,52,1),(1,255,52,1)]:
        yield make(f'link12-{word12}-{count}-{word}-{flags}',cell=record(link12=LINK12),word12=word12,byte51=count,child_word=word,child_flags=flags)
        yield make(f'partial-release-{word12}-{count}-{word}-{flags}',cell=record(link12=LINK12,link16=PRIMARY),word12=word12,byte51=count,child_word=word,child_flags=flags)
    yield make('release-before-kind-rejection',cell=record(2,flags4=64,link12=LINK12,link16=PRIMARY))
    yield make('retry-budget',cell=record(28),budget=7)
    yield make('record-prefix-preserved',cell=record(128,flags4=255,flags5=255,byte6=255))


def pipeline_cases():
    rng=random.Random(1705)
    for seed in [0,1,42,65536,0xffffffff]:
        for direction_mode in range(3):
            for pattern in ['empty','blocked','linked16','kind28','checkerboard','sparse','linked12']:
                raw=bytearray()
                for y in range(19):
                    for x in range(67):
                        if pattern=='empty':cell=record(0,byte8=0)
                        elif pattern=='blocked':cell=record(1)
                        elif pattern=='linked16':cell=record(0,byte8=0,link16=PRIMARY)
                        elif pattern=='kind28':cell=record(28)
                        elif pattern=='checkerboard':cell=record((x+y)%2)
                        elif pattern=='sparse':cell=record(0 if rng.randrange(20)==0 else 1)
                        else:cell=record(1,link12=LINK12)
                        raw.extend(cell)
                yield {'name':f'pipeline-{seed}-{direction_mode}-{pattern}','pipeline':True,'direction_mode':direction_mode,
                       'seed':seed,'fallback':42,'last':123,'budget':3,'query':1,'word16':1,'byte25':0,
                       'word12':1,'byte51':1,'child_word':1,'child_flags':0,'grid':bytes(raw)}


def execute(payloads,case):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_A5,UC_M68K_REG_A7,UC_M68K_REG_SR,UC_M68K_REG_D0,UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_PC
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x180000)
    for sid,data in payloads.items():uc.mem_write(PROFILES[sid]['base'],data)
    for displacement,segment,offset in [(0x42,1,396),(0x62,1,548),(0x136a,12,29850),(0x1372,12,29884),(0x68a,5,32110),(0x692,5,32200)]:
        uc.mem_write(A5+displacement,b'\x4e\xf9'+struct.pack('>I',PROFILES[segment]['base']+offset))
    uc.mem_write(A5-0x56fe,struct.pack('>I',case['last']));uc.mem_write(A5-0x8da,struct.pack('>H',case['fallback']))
    uc.mem_write(STOP,b'\x4e\x71');uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    call(uc,5,31998,struct.pack('>I',case['seed']),20000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('initializer instruction limit')
    raw=b'\0'*104+case['grid'];uc.mem_write(GRID,raw+b'\x5a'*16);uc.mem_write(ROW,b'\xa5\x5a\xa5\x5a')
    primary=bytearray(26);struct.pack_into('>H',primary,0,case['word16']);primary[25]=case['byte25'];uc.mem_write(PRIMARY,bytes(primary))
    child=bytearray(26);struct.pack_into('>H',child,0,case['child_word']);child[25]=case['child_flags'];uc.mem_write(CHILD,bytes(child))
    linked=bytearray(60+127*4);struct.pack_into('>H',linked,0,case['word12']);linked[51]=case['byte51']
    for i in range(127):struct.pack_into('>I',linked,60+i*4,CHILD)
    uc.mem_write(LINK12,bytes(linked))
    observed={'attempts':0};events=[]
    if case.get('pipeline'):
        mode=case['direction_mode']
        directions=(SYNTHETIC_DIRECTIONS if mode==0 else SYNTHETIC_DIRECTIONS[3:]+SYNTHETIC_DIRECTIONS[:3] if mode==1
                    else [(-128,-128),(127,127),(-128,127),(127,-128),(0,127),(127,0),(0,-128),(-128,0)])
        for index,(row,column) in enumerate(directions,1):
            uc.mem_write(A5-0x9e6+index,bytes([row&255]));uc.mem_write(A5-0x9da+index,bytes([column&255]))
    callbacks={A5+0xd7a:1,A5+0xde2:2,A5+0xb0a:3,A5+0xb1a:4}
    def hook(machine,address,size,user_data):
        if address in callbacks:
            code=callbacks[address];sp=machine.reg_read(UC_M68K_REG_A7)
            first=struct.unpack('>I',bytes(machine.mem_read(sp+4,4)))[0]
            second=struct.unpack('>I',bytes(machine.mem_read(sp+8,4)))[0] if code==3 else 0
            events.append([code,first,second])
            if code==1:machine.reg_write(UC_M68K_REG_D0,case['query'])
        elif address==PROFILES[13]['base']+0x3e6a:
            if observed['attempts']>=case['budget']:
                observed['phase']=3
                observed['row']=machine.reg_read(UC_M68K_REG_D3)&65535 if observed['attempts'] else -1
                observed['column']=machine.reg_read(UC_M68K_REG_D4)&65535 if observed['attempts'] else -1
                machine.emu_stop()
            else:observed['attempts']+=1
        elif address==PROFILES[13]['base']+15742:
            observed['pre_attempts']=(machine.reg_read(UC_M68K_REG_D5)&65535)-1
        elif address-PROFILES[13]['base'] in (0x30a8,0x3146):
            observed['phase']=4 if address-PROFILES[13]['base']==0x30a8 else 5
            observed['pre_attempts']=machine.reg_read(UC_M68K_REG_D5)&65535
        else:observed['phase']={0x3dd0:0,0x3e4c:1,0x3fb2:2}[address-PROFILES[13]['base']]
    points=[PROFILES[13]['base']+p for p in [0x3dd0,0x3e4c,0x3fb2,0x3e6a]]
    if case.get('pipeline'):points.extend(PROFILES[13]['base']+p for p in [0x30a8,0x3146,15742])
    for address in callbacks:uc.mem_write(address,b'\x4e\x75')
    for address in [*callbacks,*points]:uc.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    call(uc,13,12328 if case.get('pipeline') else 15742,struct.pack('>III',GRID,ROW,COLUMN),2000000)
    if 'phase' not in observed:raise AssertionError('fallback failed to return or hit budget boundary')
    if observed['phase']!=3:
        if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4:raise AssertionError('fallback stack/return mismatch')
        observed['row']=uc.mem_read(ROW,1)[0];observed['column']=uc.mem_read(COLUMN,1)[0]
    if bytes(uc.mem_read(GRID,104))!=raw[:104] or bytes(uc.mem_read(GRID+len(raw),16))!=b'\x5a'*16:raise AssertionError('grid boundary overwritten')
    if uc.mem_read(ROW+1,1)[0]!=0x5a or uc.mem_read(COLUMN+1,1)[0]!=0x5a:raise AssertionError('coordinate adjacent byte overwritten')
    def state(offset):return struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    prefix=[observed['phase'],observed['attempts'],observed['row'],observed['column'],state(-0x56fe),state(-0x5702),state(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400)))]
    return {'prefix':prefix,'grid':bytes(uc.mem_read(GRID+104,1273*20)),'events':events,'pre_attempts':observed.get('pre_attempts')}


def result_line(result):
    return ' '.join(map(str,result['prefix']))+' '+result['grid'].hex()+' '+str(len(result['events']))+''.join(' '+' '.join(map(str,e)) for e in result['events'])+(' '+str(result['pre_attempts']) if result['pre_attempts'] is not None else '')


def input_line(case):
    keys=['seed','fallback','last','budget','query','word16','byte25','word12','byte51','child_word','child_flags']
    return ' '.join(str(case[k]) for k in keys)+(' '+str(case['direction_mode']) if case.get('pipeline') else '')+' '+case['grid'].hex()


def verify(manifest,driver,pipeline=False):
    payloads={}
    for record,data in manifest_inputs(manifest,'CODE'):
        sid=record['id']
        if sid not in PROFILES:continue
        if sid in payloads or hashlib.sha256(data).hexdigest()!=PROFILES[sid]['sha256']:raise ValueError('ambiguous or unsupported CODE segment')
        payloads[sid]=data
    if set(payloads)!=set(PROFILES):raise ValueError('required source segments missing')
    summaries=[];inputs=[];wanted=[];phases=[0]*6;callback_count=0
    def flush():
        run=subprocess.run([str(driver.resolve()),*(['--pipeline'] if pipeline else [])],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30)
        actual=run.stdout.splitlines()
        if actual!=wanted:
            for i,(a,b) in enumerate(zip(actual,wanted)):
                if a!=b:raise AssertionError(f'native fallback mismatch near case {len(summaries)-len(wanted)+i}: {a[:100]} vs {b[:100]}')
            raise AssertionError('native fallback output count mismatch')
        inputs.clear();wanted.clear()
    for case in (pipeline_cases() if pipeline else cases()):
        result=execute(payloads,case);prefix=result['prefix'];phases[prefix[0]]+=1;callback_count+=len(result['events'])
        summaries.append({'name':case['name'],'phase':prefix[0],'random_attempts':prefix[1],'row':prefix[2],'column':prefix[3],
                          'grid_sha256':hashlib.sha256(result['grid']).hexdigest(),'callback_events':result['events']})
        inputs.append(input_line(case));wanted.append(result_line(result))
        if len(inputs)==32:flush()
    if inputs:flush()
    import unicorn
    return {'schema':1,'unicorn_version':unicorn.__version__,'cpu':'68000','routine_segment':13,'routine_offset':15742,
            'source_sha256':{str(s):p['sha256'] for s,p in PROFILES.items()},'cases':len(summaries),
            'pipeline':pipeline,'phases':dict(zip(['first-scan','second-scan','random','budget-exhausted','direct','neighbor'],phases)),
            'synthetic_callback_events':callback_count,'full_grid_and_rng_compared':True,
            'original_linked_record_callbacks_executed':False,'research_retry_budget_not_historical_limit':True,
            'original_mac_os_present':False,'full_gameplay_verified':False,'observations':summaries}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--pipeline',action='store_true');a=p.parse_args()
    repo=Path(__file__).resolve().parents[2];out=a.output.resolve()
    if out.is_relative_to(repo) and not out.is_relative_to(repo/'local-generated'):p.error('keep research outputs private')
    if out.exists():p.error('refusing to overwrite results')
    report=verify(a.manifest,a.native_driver,a.pipeline);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Passed {report["cases"]} fallback/native/grid/RNG/callback cases: {report["phases"]}; linked-record callbacks were synthetic')

if __name__=='__main__':main()

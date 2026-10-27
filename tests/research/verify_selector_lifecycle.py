#!/usr/bin/env python3
"""Original RNG/selector/lifecycle composition; only DisposePtr is observed/skipped."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_grid_selector import PROFILES as CORE, A5, GRID, STACK, STOP, ROW, COLUMN, call, SYNTHETIC_DIRECTIONS
from verify_grid_fallback import execute as baseline, record
from verify_rng_cpu import manifest_inputs

PROFILES={**CORE,
          7:{'base':0x50000,'sha256':'43eb181114493dd938496157cf0943d5fb5d152b56086fb684122fe50385e852'},
          9:{'base':0x60000,'sha256':'6212eb2b13c828c35e7593f05d15a439421dca9bdd7d6746c04f24220a96c717'},
          11:{'base':0x110000,'sha256':'a4b03764578a4d99ec8758315c15ddc2737bb454c939cc9fc0ef3695624250ca'}}
PRIMARY, CHILD, TARGET, PREVIOUS, FOLLOWING, EXTRA=0xb0000,0xb0100,0xc0000,0xc1000,0xc2000,0xd0000
KEYS=('seed','directions','profile','shape','prefix','word','flags','count','row','column','position')


def cases(payloads,startup=False):
    words=[0,1,29,52,70,81,175,65535]
    for si,seed in enumerate([0,42,0xffffffff]):
        for direction in range(1 if startup else 3):
            # Authored target uses the first original fallback draw on an all-
            # rejected map. Any earlier native/original discrepancy still changes
            # the compared output; target selection is not an expected result.
            sample={'seed':seed,'fallback':42,'last':123,'budget':1,'query':1,'word16':1,'byte25':0,
                    'word12':1,'byte51':0,'child_word':1,'child_flags':0,'grid':record()*1273,
                    'pipeline':True,'direction_mode':direction}
            initial=baseline({sid:payloads[sid] for sid in CORE},sample)['prefix']
            row,column=initial[2:4]
            for profile in range(9):
                for shape in range(2):
                    for pi,prefix in enumerate([65535,0,0x1234]):
                        yield dict(zip(KEYS,[seed,direction,profile,shape,prefix,
                            words[(si*27+profile*3+direction+shape+pi)%len(words)],
                            int((profile+direction+shape+pi)%5==0),(profile+direction+shape)%4,
                            row,column,(si+direction+profile+shape)%3]))


def make_world(c):
    records={PRIMARY+i*0x100:bytearray(b'\xa5'*64) for i in range(5)}
    records.update({identity:bytearray(b'\xa5'*568) for identity in (TARGET,PREVIOUS,FOLLOWING)})
    records[EXTRA]=bytearray(b'\xa5'*16)
    def put(b,at,value):struct.pack_into('>I',b,at,value)
    for i in range(5):
        b=records[PRIMARY+i*0x100];struct.pack_into('>H',b,0,1);b[25]=0;put(b,26,0);put(b,30,0)
    p=records[PRIMARY];struct.pack_into('>H',p,0,c['word']);p[25]=c['flags']
    if c['shape']:
        put(p,26,CHILD);put(p,30,CHILD+0x200);put(records[CHILD],26,CHILD+0x100);put(records[CHILD],30,CHILD+0x300)
    for identity in (TARGET,PREVIOUS,FOLLOWING):
        b=records[identity];struct.pack_into('>H',b,0,1);b[48]=b[49]=1;b[51]=0
        put(b,52,0);put(b,56,0)
        for i in range(127):put(b,60+i*4,0)
    parent=records[TARGET];parent[48]=c['row'];parent[49]=c['column'];parent[51]=c['count'];put(parent,52,EXTRA)
    for i in range(c['count']):put(parent,60+i*4,CHILD+(i%4)*0x100)
    if c['profile']==5:parent[1]=73
    if c['profile']==6:records[CHILD][1]=52
    head=TARGET if c['position']==0 else PREVIOUS
    if c['position']==0:put(parent,56,PREVIOUS);put(records[PREVIOUS],56,FOLLOWING)
    elif c['position']==1:put(records[PREVIOUS],56,TARGET);put(parent,56,FOLLOWING)
    else:put(records[PREVIOUS],56,FOLLOWING);put(records[FOLLOWING],56,TARGET)
    grid=bytearray()
    for row in range(19):
        for column in range(67):
            cell=record()
            if c['profile']==0 or (c['profile']==1 and (row+column)%2==0):cell=record(0,byte8=0)
            grid.extend(cell)
    start=(c['row']*67+c['column'])*20
    if c['profile']>=2:
        if c['profile']==2:cell=record(0,byte8=0,link16=PRIMARY)
        elif c['profile']==7:cell=record(0,byte8=0)
        else:cell=record(2 if c['profile']==4 else 25 if c['profile']==8 else 1,
                         flags4=64 if c['profile']==4 else 0,link16=PRIMARY,link12=TARGET)
        grid[start:start+20]=cell
    header=bytearray(104);struct.pack_into('>HI',header,18,3,head)
    return bytes(header+grid),records


def execute(payloads,c,startup=None):
    from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
    from unicorn.m68k_const import UC_CPU_M68K_M68000,UC_M68K_REG_A5,UC_M68K_REG_A7,UC_M68K_REG_SR,UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_PC,UC_M68K_REG_A0
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000);uc.mem_map(0x10000,0x180000)
    for sid,data in payloads.items():uc.mem_write(PROFILES[sid]['base'],data)
    uc.reg_write(UC_M68K_REG_SR,0x2000)
    if startup:
        from verify_a5_initialization import initialize_in_context
        initialize_in_context(uc,startup,A5)
    stubs=[(0x42,1,396),(0x62,1,548),(0x136a,12,29850),(0x1372,12,29884),(0x68a,5,32110),(0x692,5,32200),
           (0xd7a,9,27148),(0xde2,9,28968),(0xb0a,7,3872),(0xb1a,7,4104),(0x1312,11,454)]
    for displacement,segment,offset in stubs:uc.mem_write(A5+displacement,b'\x4e\xf9'+struct.pack('>I',PROFILES[segment]['base']+offset))
    uc.mem_write(A5-0x56fe,struct.pack('>I',123));uc.mem_write(A5-0x8da,struct.pack('>H',42))
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    call(uc,5,31998,struct.pack('>I',c['seed']),20000)
    if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('initializer failed')
    directions=SYNTHETIC_DIRECTIONS if c['directions']==0 else SYNTHETIC_DIRECTIONS[3:]+SYNTHETIC_DIRECTIONS[:3] if c['directions']==1 else [(-128,-128),(127,127),(-128,127),(127,-128),(0,127),(127,0),(0,-128),(-128,0)]
    if not startup:
        for index,(row,column) in enumerate(directions,1):
            uc.mem_write(A5-0x9e6+index,bytes([row&255]));uc.mem_write(A5-0x9da+index,bytes([column&255]))
    initial,records=make_world(c);uc.mem_write(GRID,initial+b'\x5a'*16)
    for identity,data in records.items():
        uc.mem_write(identity-18,b'\xa5'*16+struct.pack('>H',c['prefix'])+bytes(data)+b'\x5a'*16)
    uc.mem_write(ROW,b'\xa5\x5a\xa5\x5a');events=[];observed={'attempts':0,'pre':0}
    callbacks={A5+0xd7a:1,A5+0xde2:2,A5+0xb0a:3,A5+0xb1a:4,A5+0x1312:5}
    trap=PROFILES[11]['base']+470
    def hook(machine,address,size,user):
        if address in callbacks:
            code=callbacks[address];sp=machine.reg_read(UC_M68K_REG_A7)
            first=struct.unpack('>I',bytes(machine.mem_read(sp+4,4)))[0]
            second=(struct.unpack('>I',bytes(machine.mem_read(sp+8,4)))[0] if code==3 else
                    struct.unpack('>H',bytes(machine.mem_read(first-2,2)))[0] if code==5 else 0)
            events.append([code,first,second])
        elif address==trap:
            events.append([6,machine.reg_read(UC_M68K_REG_A0),0]);machine.reg_write(UC_M68K_REG_PC,trap+2)
        elif address==PROFILES[13]['base']+0x3e6a:
            if observed['attempts']==1:
                observed.update(phase=3,row=machine.reg_read(UC_M68K_REG_D3)&65535,column=machine.reg_read(UC_M68K_REG_D4)&65535);machine.emu_stop()
            else:observed['attempts']+=1
        elif address==PROFILES[13]['base']+15742:observed['pre']=(machine.reg_read(UC_M68K_REG_D5)&65535)-1
        elif address-PROFILES[13]['base'] in (0x30a8,0x3146):
            observed['phase']=4 if address-PROFILES[13]['base']==0x30a8 else 5;observed['pre']=machine.reg_read(UC_M68K_REG_D5)&65535
        else:observed['phase']={0x3dd0:0,0x3e4c:1,0x3fb2:2}[address-PROFILES[13]['base']]
    points=[PROFILES[13]['base']+offset for offset in (0x3dd0,0x3e4c,0x3fb2,0x3e6a,15742,0x30a8,0x3146)]
    for point in [*callbacks,trap,*points]:uc.hook_add(UC_HOOK_CODE,hook,begin=point,end=point)
    call(uc,13,12328,struct.pack('>III',GRID,ROW,COLUMN),2000000)
    if 'phase' not in observed:raise AssertionError('selector instruction limit')
    if observed['phase']!=3:
        if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4:raise AssertionError('selector return/stack')
        observed.update(row=uc.mem_read(ROW,1)[0],column=uc.mem_read(COLUMN,1)[0])
    after=bytes(uc.mem_read(GRID,len(initial)))
    if after[:18]!=initial[:18] or after[24:104]!=initial[24:104] or bytes(uc.mem_read(GRID+len(initial),16))!=b'\x5a'*16:raise AssertionError('grid/header guard overwritten')
    if uc.mem_read(ROW+1,1)[0]!=0x5a or uc.mem_read(COLUMN+1,1)[0]!=0x5a:raise AssertionError('coordinate guard overwritten')
    state=lambda offset:struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    numbers=[observed['phase'],observed['attempts'],observed['row'],observed['column'],observed['pre'],state(-0x56fe),state(-0x5702),state(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400))),*struct.unpack_from('>HI',after,18)]
    parts=[' '.join(map(str,numbers)),after[104:].hex()]
    for identity,data in sorted(records.items()):
        if bytes(uc.mem_read(identity-18,16))!=b'\xa5'*16 or bytes(uc.mem_read(identity+len(data),16))!=b'\x5a'*16:raise AssertionError('record boundary overwritten')
        parts.extend([str(identity),str(struct.unpack('>H',bytes(uc.mem_read(identity-2,2)))[0]),bytes(uc.mem_read(identity,len(data))).hex()])
    parts.append(str(len(events)))
    for event in events:parts.extend(map(str,event))
    return ' '.join(parts),observed,len(events)


def verify(manifest,driver,startup_data=False):
    payloads={}
    for rec,data in manifest_inputs(manifest,'CODE'):
        sid=rec['id']
        if sid not in PROFILES:continue
        if sid in payloads or hashlib.sha256(data).hexdigest()!=PROFILES[sid]['sha256']:raise ValueError('unsupported source segment')
        payloads[sid]=data
    if set(payloads)!=set(PROFILES):raise ValueError('source segment missing')
    inputs=[];wanted=[];summaries=[];startup=None
    if startup_data:
        from verify_a5_initialization import sources,startup_image
        startup=sources(manifest);image,below,above=startup_image(startup)
        pairs=[(int.from_bytes(image[below-2534+i:below-2534+i+1],signed=True),int.from_bytes(image[below-2522+i:below-2522+i+1],signed=True)) for i in range(1,9)]
        if pairs!=SYNTHETIC_DIRECTIONS:raise AssertionError('baseline fixture directions differ from recovered startup values')
        inputs.append(f'{below} {above} {startup["DATA"].hex()} {startup["ZERO"].hex()} {startup["DREL"].hex()}')
    for c in cases(payloads,startup_data):
        inputs.append(' '.join(str(c[k]) for k in KEYS));line,observed,events=execute(payloads,c,startup);wanted.append(line)
        summaries.append({'config':c,'outcome':observed,'events':events,'result_sha256':hashlib.sha256(line.encode()).hexdigest()})
    run=subprocess.run([str(driver.resolve()),*(['--startup-data'] if startup_data else [])],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=60)
    actual=run.stdout.splitlines()
    if len(actual)!=len(wanted):raise AssertionError('native result count')
    for index,(a,b) in enumerate(zip(actual,wanted)):
        if a!=b:
            first=next(i for i,(x,y) in enumerate(zip(a.split(),b.split())) if x!=y)
            raise AssertionError(f'composition mismatch case {index}, token {first}: {a.split()[first][:90]} != {b.split()[first][:90]}; {summaries[index]["config"]}')
    import unicorn
    return {'schema':1,'unicorn_version':unicorn.__version__,'source_profiles':PROFILES,'cases':len(wanted),
            'scope':'Original selector and recovered lifecycle composition on authored worlds; DisposePtr observed/skipped',
            'direction_origin':'original DATA/ZERO/DREL startup' if startup_data else 'supplied synthetic tables',
            'phase_counts':{p:sum(s['outcome']['phase']==p for s in summaries) for p in range(6)},'results':summaries}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--startup-directions',action='store_true')
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original-derived evidence private')
    report=verify(a.manifest,a.native_driver,a.startup_directions);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} original selector/lifecycle cases: {report["phase_counts"]}')


if __name__=='__main__':main()

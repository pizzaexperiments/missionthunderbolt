#!/usr/bin/env python3
"""Check the null-old-chain helper with five explicitly supplied allocations.

Executes original helper, child-factory and RNG instructions except five allocator
JSR boundaries: each is stopped before execution, D0 receives a supplied payload,
and execution resumes at the original movea.l d0,a4. No allocator or OS behavior
is claimed; factory and RNG results are never substituted.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_child_record_prefix import SOURCES, forced_table, template, BRANCHES, RETURN_OFFSETS
from verify_grid_selector import A5, STACK, STOP, call
from verify_record_factory_tail import BASE
from verify_rng_cpu import PROFILES, manifest_inputs
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.m68k_const import (UC_CPU_M68K_M68000, UC_M68K_REG_SR, UC_M68K_REG_PC,
    UC_M68K_REG_A0, UC_M68K_REG_A3, UC_M68K_REG_A4, UC_M68K_REG_A5,
    UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_D0)

TABLE,EXTERNAL=0xd0000,0xf0000
VARIANTS=(31,27,28,37,72)
BOUNDS=(200,50,50,200,25)
BIASES=(200,25,25,100,25)
FACTORY_RETURNS=(0x4e26,0x4e44,0x4e66,0x4e88,0x4eaa)
HELPER_RETURNS=(0x4e30,0x4e54,0x4e76,0x4e98,0x4eba)
CONTEXT_BRANCHES={0x4a36:'lookup',0x4a78:'lookup_eligible',0x4a88:'lookup_replace',
    0x4b9c:'factor',0x4c9e:'counter'}


def cases():
    random_source=random.Random(3600)
    def make(seed=42,values=None,records=None,lookup=255):
        fallback,shuffle=forced_table(values) if values is not None else (42,[0]*100)
        parent=bytearray(random_source.randrange(256) for _ in range(56));struct.pack_into('>I',parent,30,0)
        t=records or [template(v,1,65535,1,0) for v in VARIANTS]
        return {'seed':seed,'fallback':fallback,'last':0x89abcdef,'mode':int(values is not None),'warmup':0,
                'shuffle':shuffle,'parent_handle':0xb0000,'handles':[0xc0000+i*0x100 for i in range(5)],
                'parent':bytes(parent),'children':[bytes(random_source.randrange(256) for _ in range(56)) for _ in range(5)],
                'templates':t,'lookup':bytes([lookup])*50,'factor_word':0x8001,'counter':65535,
                'address_base':0xfffffff0,'factor42':65535}
    for value in range(256):
        index=value%50
        for gate in (0,4):
            c=make(values=[0,0,0,index,gate,2,0,0],lookup=value)
            lookup=bytearray([2]*50);lookup[index]=value;c['lookup']=bytes(lookup)
            yield c
    supported=(0,25,39,62,63,81,100,108,109,114,116,127,129,137,138,144,77,37)
    for seed in range(256):
        records=[]
        for i in range(5):
            r=bytearray(template(supported[(seed+i)%len(supported)],(1,3,32767)[(seed+i)%3],
                                 (0,32767,32768,65535)[(seed+i)%4],(1,127,128,255)[(seed+i)%4],32))
            struct.pack_into('>H',r,22,(0,3,32768,65535)[(seed+i)%4]);r[7]=(0,127,128,255)[(seed+i)%4]
            records.append(bytes(r))
        c=make(seed=seed,records=records,lookup=seed)
        c['counter']=(seed*257)&65535;c['address_base']=(seed*0x10000001)&0xffffffff
        c['factor_word']=(0,1,32767,32768,65535)[seed%5];c['warmup']=seed%5
        # A different supplied identity order verifies links use handles, not slot arithmetic.
        shift=seed%5;c['handles']=c['handles'][shift:]+c['handles'][:shift]
        yield c
    # Exact lower and upper helper overwrite values without recomputing word14.
    for upper in (False,True):
        records=[template(0,1,32768,1,0) for _ in range(5)]
        yield make(records=records,values=[b-1 if upper else 0 for b in BOUNDS])
    # One maximum eleven-draw factory case, surrounded by the other helper calls.
    records=[template(0,1,1,1,0) for _ in range(5)]
    records[3]=template(37,3,32768,1,32)
    c=make(records=records,values=[0,0,0,2,1,0,9,1,0,0,2,49,0,2,0,0])
    c['lookup']=bytes([2]*49+[255]);yield c


def original(sources,c):
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x180000)
    for sid,base in ((1,0x10000),(12,0x20000),(5,0x30000),(9,BASE)):uc.mem_write(base,sources[sid])
    services=((0x42,1,396),(0x62,1,548),(0x136a,12,29850),
              (0x1372,12,29884),(0x68a,5,32110),(0x692,5,32200))
    allowed={A5+offset for offset,_,_ in services}
    for offset,sid,entry in services:uc.mem_write(A5+offset,b'\x4e\xf9'+struct.pack('>I',PROFILES[sid]['base']+entry))
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    uc.mem_write(A5-0x56fe,struct.pack('>I',c['last']));uc.mem_write(A5-0x8da,struct.pack('>H',c['fallback']))
    if c['mode']==0:
        call(uc,5,31998,struct.pack('>I',c['seed']),20000)
        if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('initializer endpoint')
    else:
        uc.mem_write(A5-0x5702,struct.pack('>II100I',c['seed'],c['last'],*c['shuffle']))
        uc.mem_write(A5-0xb26,struct.pack('>I',c['fallback']))
    for _ in range(c['warmup']):
        call(uc,5,32110,struct.pack('>H',1),20000)
        if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('warmup endpoint')
    table=bytearray((i*17+j*31)&255 for i in range(137) for j in range(56))
    struct.pack_into('>H',table,42*56+14,c['factor42'])
    for v,r in zip(VARIANTS,c['templates']):table[v*56:(v+1)*56]=r
    table_guard=b'\x5a'*16+bytes(table)+b'\x5a'*16;uc.mem_write(TABLE-16,table_guard)
    pointer_guard=b'\xa5'*8+struct.pack('>I',TABLE)+b'\xa5'*8;uc.mem_write(A5-0x2626-8,pointer_guard)
    lookup_guard=b'\xa5'*8+c['lookup']+b'\xa5'*8;uc.mem_write(A5-0x19af-8,lookup_guard)
    external=bytearray(b'\xa5'*0x1190);struct.pack_into('>H',external,0x118e,c['factor_word'])
    external_guard=b'\x5a'*16+bytes(external)+b'\x5a'*16;uc.mem_write(EXTERNAL-16,external_guard)
    ext_pointer_guard=b'\xa5'*8+struct.pack('>I',EXTERNAL)+b'\xa5'*8;uc.mem_write(A5-0x1a48-8,ext_pointer_guard)
    global_guard=b'\xa5'*8+struct.pack('>HI',c['counter'],c['address_base'])+b'\xa5'*8
    uc.mem_write(A5-0x9f8-8,global_guard)
    parent=c['parent_handle'];uc.mem_write(parent-16,b'\xcc'*16+c['parent']+b'\xcc'*16)
    for h,r in zip(c['handles'],c['children']):uc.mem_write(h-16,b'\xcc'*16+r+b'\xcc'*16)
    for address,size in ((A5-0x5702,408),(A5-0xb26,4)):
        uc.mem_write(address-16,b'\x5a'*16);uc.mem_write(address+size,b'\x5a'*16)
    stack_header=struct.pack('>II',STOP,parent)
    uc.mem_write(STACK-1024,b'\x5a'*16);uc.mem_write(STACK,stack_header+b'\x5a'*16)
    saved={UC_M68K_REG_A3:0x12345678,UC_M68K_REG_A4:0x23456780,UC_M68K_REG_A6:0x34567890}
    for reg,value in saved.items():uc.reg_write(reg,value)
    uc.reg_write(UC_M68K_REG_A7,STACK)
    draws=[];pending=[];allocations=[];factory_counts=[];coverage=Counter();state={'active':None,'draw_start':0,'boundary':False}
    branches={**BRANCHES,**CONTEXT_BRANCHES}
    returns=set(RETURN_OFFSETS)|{0x4aae,0x4ac0,0x4ad2,0x4aec,0x4b14,0x4b26,0x4b38,0x4b4a,0x4b5c,0x4bec,0x4c0e,0x4a3e,0x4a80,0x4a90,0x4cb0,*HELPER_RETURNS}
    ranges=[(STACK-1008,STACK),(parent+30,parent+34),(A5-0x5702,A5-0x5702+408),
            (A5-0xb26,A5-0xb26+4),(A5-0x9f8,A5-0x9f8+2)]+[(h,h+56) for h in c['handles']]
    def write(machine,access,address,size,value,user):
        if not any(start<=address and address+size<=end for start,end in ranges):raise AssertionError('write outside permitted chain state')
    def service(machine,address):
        if address not in allowed:raise AssertionError('unmodeled original service')
        if address in (A5+0x68a,A5+0x692):
            if pending:raise AssertionError('nested RNG draw')
            sp=machine.reg_read(UC_M68K_REG_A7);bound=struct.unpack('>H',bytes(machine.mem_read(sp+4,2)))[0]
            pending.append([bound,int(address==A5+0x692)])
        elif not pending:raise AssertionError('RNG helper outside draw')
    def code(machine,address,size,user):
        if A5+32<=address<=A5+6335:service(machine,address);return
        if not BASE<=address<BASE+len(sources[9]):return
        offset=address-BASE
        if not (0x4834<=offset<=0x4ce0 or 0x4e00<=offset<=0x4eca):raise AssertionError('unmodeled CODE9 instruction')
        if offset in branches:coverage[branches[offset]]+=1
        if offset==0x4834:
            i=len(allocations)
            if i>=5 or state['active'] is not None:raise AssertionError('unexpected child factory entry')
            sp=machine.reg_read(UC_M68K_REG_A7)
            if bytes(machine.mem_read(sp,8))!=struct.pack('>IHH',BASE+FACTORY_RETURNS[i],1,VARIANTS[i]):raise AssertionError('factory call order/packed ABI')
            state.update(active=i,draw_start=len(draws))
        elif offset==0x4848:
            i=state['active'];sp=machine.reg_read(UC_M68K_REG_A7)
            if i!=len(allocations) or bytes(machine.mem_read(sp,8))!=struct.pack('>II',1,56):raise AssertionError('supplied allocator arguments/order')
            state['boundary']=True;machine.emu_stop()
        elif offset==0x487e:
            i=state['active']
            if machine.reg_read(UC_M68K_REG_A4)!=c['handles'][i] or bytes(machine.mem_read(c['handles'][i],56))!=c['templates'][i]:raise AssertionError('child copy')
            if machine.reg_read(UC_M68K_REG_A0)!=TABLE+(VARIANTS[i]+1)*56:raise AssertionError('copy source slot')
        elif offset in FACTORY_RETURNS:
            i=FACTORY_RETURNS.index(offset)
            if state['active']!=i or machine.reg_read(UC_M68K_REG_D0)!=c['handles'][i]:raise AssertionError('factory return/order')
            factory_counts.append(len(draws)-state['draw_start']);state['active']=None
        if offset in returns:
            if len(pending)!=1:raise AssertionError('unpaired RNG return')
            draw=pending.pop()+[machine.reg_read(UC_M68K_REG_D0)&65535];draws.append(draw)
            if offset in HELPER_RETURNS:
                i=HELPER_RETURNS.index(offset)
                if len(factory_counts)!=i+1 or draw[:2]!=[BOUNDS[i],1]:raise AssertionError('helper draw order/bound')
    uc.hook_add(UC_HOOK_MEM_WRITE,write);uc.hook_add(UC_HOOK_CODE,code)
    uc.ctl_flush_tb();pc=BASE+0x4e00
    for _ in range(6):
        state['boundary']=False;uc.emu_start(pc,STOP,count=500000)
        if state['boundary']:
            if uc.reg_read(UC_M68K_REG_PC)!=BASE+0x4848:raise AssertionError('allocator substitution did not stop before JSR')
            i=len(allocations);allocations.append(c['handles'][i])
            # Explicit supplied-allocation substitution, not original allocator behavior.
            uc.reg_write(UC_M68K_REG_D0,c['handles'][i]);pc=BASE+0x484c
        elif uc.reg_read(UC_M68K_REG_PC)==STOP:break
        else:raise AssertionError('unexpected chain endpoint/instruction budget')
    if len(allocations)!=5 or len(factory_counts)!=5 or pending or state['active'] is not None:raise AssertionError('chain completion/balance')
    expected_regs={**saved,UC_M68K_REG_A5:A5,UC_M68K_REG_A7:STACK+4,UC_M68K_REG_PC:STOP}
    if any(uc.reg_read(reg)!=value for reg,value in expected_regs.items()):raise AssertionError('helper return/register ABI')
    if bytes(uc.mem_read(STACK,8))!=stack_header or bytes(uc.mem_read(STACK-1024,16))!=b'\x5a'*16 or bytes(uc.mem_read(STACK+8,16))!=b'\x5a'*16:raise AssertionError('stack header/guards')
    for address,size in ((A5-0x5702,408),(A5-0xb26,4)):
        if bytes(uc.mem_read(address-16,16))!=b'\x5a'*16 or bytes(uc.mem_read(address+size,16))!=b'\x5a'*16:raise AssertionError('RNG guards')
    for address,expected in ((TABLE-16,table_guard),(A5-0x2626-8,pointer_guard),
        (A5-0x19af-8,lookup_guard),(EXTERNAL-16,external_guard),(A5-0x1a48-8,ext_pointer_guard)):
        if bytes(uc.mem_read(address,len(expected)))!=expected:raise AssertionError('source/context guards')
    counter_increments=sum(struct.unpack_from('>H',r)[0] in (137,138) for r in c['templates'])
    counter=(c['counter']+counter_increments)&65535;expected_global=bytearray(global_guard);struct.pack_into('>H',expected_global,8,counter)
    if bytes(uc.mem_read(A5-0x9f8-8,len(global_guard)))!=bytes(expected_global):raise AssertionError('context mutation/guards')
    output=[]
    for handle in [parent,*c['handles']]:
        if bytes(uc.mem_read(handle-16,16))!=b'\xcc'*16 or bytes(uc.mem_read(handle+56,16))!=b'\xcc'*16:raise AssertionError('record guards')
        output.append(bytes(uc.mem_read(handle,56)))
    expected_parent=bytearray(c['parent']);struct.pack_into('>I',expected_parent,30,c['handles'][0])
    if output[0]!=bytes(expected_parent):raise AssertionError('parent mutation')
    if struct.unpack_from('>I',output[-1],26)[0]!=struct.unpack_from('>I',c['templates'][-1],26)[0]:raise AssertionError('last copied next link retention')
    for i in range(4):
        if struct.unpack_from('>I',output[i+1],26)[0]!=c['handles'][i+1]:raise AssertionError('chain link order')
    for i,r in enumerate(output[1:]):
        if not BIASES[i]+1<=struct.unpack_from('>H',r,10)[0]<=BIASES[i]+BOUNDS[i]:raise AssertionError('post-factory count range')
    for sid,base in ((1,0x10000),(12,0x20000),(5,0x30000),(9,BASE)):
        if bytes(uc.mem_read(base,len(sources[sid])))!=sources[sid]:raise AssertionError('original code changed')
    state_word=lambda offset:struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    numbers=[state_word(-0x56fe),state_word(-0x5702),state_word(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400)))]
    line=' '.join(r.hex() for r in output)+' '+' '.join(map(str,numbers))+f' {counter} {len(draws)}'+''.join(' '+' '.join(map(str,d)) for d in draws)+' '+' '.join(map(str,factory_counts))
    return line,len(draws),factory_counts,coverage


def verify(manifest,driver):
    sources={}
    for resource,data in manifest_inputs(manifest,'CODE'):
        sid=resource['id']
        if sid not in SOURCES:continue
        if sid in sources or hashlib.sha256(data).hexdigest()!=SOURCES[sid]:raise ValueError('ambiguous/unsupported CODE source')
        sources[sid]=data
    if set(sources)!=set(SOURCES):raise ValueError('required CODE sources missing')
    inputs=[];wanted=[];count=0;draws=0;maximum=0;factory_max=0;coverage=Counter();digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native output count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:
                aa,bb=a.split(),b.split();token=next((j for j,(x,y) in enumerate(zip(aa,bb)) if x!=y),min(len(aa),len(bb)))
                raise AssertionError(f'chain mismatch case {count-len(wanted)+i}, token {token}')
        inputs.clear();wanted.clear()
    for c in cases():
        line,n,factory_counts,blocks=original(sources,c);wanted.append(line);count+=1;draws+=n;maximum=max(maximum,n);factory_max=max(factory_max,max(factory_counts));coverage.update(blocks);digest.update((line+'\n').encode())
        inputs.append(' '.join(str(c[k]) for k in ('mode','seed','fallback','last','warmup','parent_handle'))+' '+' '.join(map(str,c['handles']))+
                      ' '+c['lookup'].hex()+' '+' '.join(str(c[k]) for k in ('factor_word','counter','address_base','factor42'))+
                      ' '+c['parent'].hex()+' '+' '.join(r.hex() for r in c['children'])+' '+' '.join(r.hex() for r in c['templates'])+
                      (' '+' '.join(map(str,c['shuffle'])) if c['mode'] else ''))
        if len(inputs)==64:flush()
    flush()
    if factory_max!=11 or not {'lookup','lookup_eligible','lookup_replace','factor','counter'}<=set(coverage):raise AssertionError('required connected context coverage')
    import unicorn
    return {'schema':1,'source_sha256':SOURCES,'unicorn_version':unicorn.__version__,'cases':count,'children':count*5,
            'rng_draws':draws,'maximum_draws_per_case':maximum,'maximum_factory_draws':factory_max,
            'allocator_boundary_substitutions':count*5,'allocator_jsr_skips_per_case':5,'allocator_arguments':[1,56],
            'boundary_stop_offset':0x4848,'supplied_register':'D0','resume_offset':0x484c,
            'original_allocator_executed':False,'old_chain_release_executed':False,
            'executed_blocks':dict(sorted(coverage.items())),'result_sha256':digest.hexdigest(),
            'scope':'CODE9 helper4e00..4eca and actual childfactory/RNG instructions, except five explicit supplied-allocation JSR substitutions; null oldparent+30, authored templates/context/records; no allocator/OS/freeing/wholefactory/gameplay claim'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path)
    p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} child-chain cases, {report["children"]} supplied children and {report["rng_draws"]} draws')


if __name__=='__main__':main()

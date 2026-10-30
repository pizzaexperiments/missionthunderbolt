#!/usr/bin/env python3
"""Compare the bounded supplied-allocation child prefix with original instructions.

No allocator, child type dispatch, whole factory or original gameplay is modeled.
Only lawfully supplied, hash-checked local resources are read; reports stay private.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from verify_record_factory_tail import SOURCES, BASE, CELL, FRAME
from verify_grid_selector import A5, STACK, STOP, call
from verify_rng_cpu import PROFILES, manifest_inputs
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.m68k_const import (UC_CPU_M68K_M68000, UC_M68K_REG_SR,
    UC_M68K_REG_A0, UC_M68K_REG_A4, UC_M68K_REG_A5, UC_M68K_REG_A6,
    UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_D6, UC_M68K_REG_PC)

TABLE=0xd0000
BRANCHES={0x4886:'count_draw',0x48ce:'word_add',0x48ec:'word_subtract',
          0x4902:'word_signed_clamp',0x4924:'byte_increment_one',
          0x492a:'byte_increment_random',0x4956:'byte_decrement_one',
          0x495c:'byte_decrement_random',0x4970:'byte_signed_clamp'}
RETURN_OFFSETS=(0x488e,0x48c8,0x48d6,0x48e6,0x48f4,0x4910,0x491e,0x4932,0x4942,0x4950,0x4964)


def template(kind=3,count=1,word=1,byte=1,flags=32):
    record=bytearray((j*31+17)&255 for j in range(56))
    for offset,value in ((0,kind),(10,count),(14,word)):struct.pack_into('>H',record,offset,value)
    record[6]=byte;record[24]=flags
    return bytes(record)


def forced_table(values,seed=42):
    """Choose authored shuffle entries, not service return shims or patched code."""
    for selector in range(seed,seed+10000):
        s=selector;indices=[]
        for _ in values:
            s=(s*1103515245+12345)&0xffffffff
            indices.append(((s>>16)&32767)%100)
        if len(indices)==len(set(indices)):
            table=[123]*100
            for i,value in zip(indices,values):table[i]=value
            return selector,table
    raise AssertionError('cannot author distinct shuffle slots')


def cases():
    rng=random.Random(3108)
    def make(t,variant=0,mode=0,seed=42,warmup=0,values=None):
        fallback=42;shuffle=[0]*100
        if values is not None:fallback,shuffle=forced_table(values);mode=1
        return {'template':t,'variant':variant,'mode':mode,'seed':seed,'fallback':fallback,
                'last':0x89abcdef,'warmup':warmup,'shuffle':shuffle,
                'record':bytes(rng.randrange(256) for _ in range(56))}
    # All actual templates and representative out-of-range nonnegative words.
    for variant in list(range(137))+[137,138,255,256,16384,32767]:
        yield make(template(count=1,flags=0),variant)
    # Signed count branches, multiplication wrap and early-exit flag/byte gates.
    for count in (0,1,2,3,32767,32768,65535):
        for word in (0,1,32767,32768,65535):
            for byte,flags in ((0,32),(1,0),(127,2),(128,34),(255,255)):
                yield make(template(count=count,word=word,byte=byte,flags=flags),seed=count+word)
    # Initialized RNG explores independently changing draws and full table state.
    for seed in range(1024):
        yield make(template(count=(1,2,32767)[seed%3],word=(1,32767,32768,65535)[seed%4],
                            byte=(1,2,127,128,254,255)[seed%6],flags=(32,34)[seed%2]),
                   variant=seed%137,seed=seed,warmup=(seed%5)*8)
    # Fixed authored input states guarantee every arithmetic/clamp block executes.
    for word in (0,1,2,32767,32768,65535):
        for delta in (0,9):
            yield make(template(word=word),values=[0,delta,1,1])
            yield make(template(word=word),values=[1,0,delta,1,1])
    byte_paths=([0,1],[0,0,0],[0,0,2],[1,0,1],[1,0,0,0],[1,0,0,2],[1,1])
    for byte in (1,2,3,127,128,129,254,255):
        for values in byte_paths:
            yield make(template(word=65535,byte=byte,flags=34),values=values)
    # Count + word subtraction + random byte subtraction is the eight-draw path.
    yield make(template(count=3,word=32768,byte=1),variant=136,
               values=[2,1,0,9,1,0,0,2])
    # Kind 71 also suppresses only the word perturbation; bit 5 still gates both.
    for flags in (0,2,32,34,255):
        for values in byte_paths:
            yield make(template(kind=71,byte=255,flags=flags),values=values)


def original(sources,c,*,factory=False,context=None):
    """Default stops before dispatch; factory=True explicitly enables its oracle."""
    if context is not None and not factory:raise ValueError('context requires explicit factory mode')
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000,0x180000)
    for sid,base in ((1,0x10000),(12,0x20000),(5,0x30000),(9,BASE)):uc.mem_write(base,sources[sid])
    services=((0x42,1,396),(0x62,1,548),(0x136a,12,29850),
              (0x1372,12,29884),(0x68a,5,32110),(0x692,5,32200))
    allowed={A5+offset for offset,_,_ in services}
    for offset,sid,entry in services:
        uc.mem_write(A5+offset,b'\x4e\xf9'+struct.pack('>I',PROFILES[sid]['base']+entry))
    uc.reg_write(UC_M68K_REG_SR,0x2000);uc.reg_write(UC_M68K_REG_A5,A5)
    uc.mem_write(A5-0x56fe,struct.pack('>I',c['last']))
    uc.mem_write(A5-0x8da,struct.pack('>H',c['fallback']))
    if c['mode']==0:
        call(uc,5,31998,struct.pack('>I',c['seed']),20000)
        if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('initializer endpoint')
    else:
        uc.mem_write(A5-0x5702,struct.pack('>II100I',c['seed'],c['last'],*c['shuffle']))
        uc.mem_write(A5-0xb26,struct.pack('>I',c['fallback']))
    for _ in range(c['warmup']):
        call(uc,5,32110,struct.pack('>H',1),20000)
        if uc.reg_read(UC_M68K_REG_PC)!=STOP:raise AssertionError('warmup endpoint')
    selected=c['variant'] if c['variant']<=136 else 0
    table=bytearray((i*17+j*31)&255 for i in range(137) for j in range(56))
    if factory:struct.pack_into('>H',table,42*56+14,c['factor'])
    table[selected*56:(selected+1)*56]=c['template'];table=bytes(table)
    guarded_table=b'\x5a'*16+table+b'\x5a'*16
    uc.mem_write(TABLE-16,guarded_table)
    pointer_context=b'\xa5'*8+struct.pack('>I',TABLE)+b'\xa5'*8
    uc.mem_write(A5-0x2626-8,pointer_context)
    if context is not None:
        if len(context['lookup'])!=50:raise ValueError('lookup must contain 50 authored bytes')
        lookup_context=b'\xa5'*8+context['lookup']+b'\xa5'*8
        external=bytearray(b'\xa5'*0x1190);struct.pack_into('>H',external,0x118e,context['factor_word'])
        external_context=b'\x5a'*16+bytes(external)+b'\x5a'*16
        external_pointer=b'\xa5'*8+struct.pack('>I',0xf0000)+b'\xa5'*8
        counter_context=b'\xa5'*8+struct.pack('>HI',context['counter'],context['address_base'])+b'\xa5'*8
        uc.mem_write(A5-0x19af-8,lookup_context)
        uc.mem_write(0xf0000-16,external_context)
        uc.mem_write(A5-0x1a48-8,external_pointer)
        uc.mem_write(A5-0x9f8-8,counter_context)
    uc.mem_write(CELL-16,b'\xcc'*16+c['record']+b'\xcc'*16)
    level=c['level']&65535 if factory else 0x1234
    frame=bytearray(b'\xa5'*64);struct.pack_into('>H',frame,26,c['variant'])
    if factory:struct.pack_into('>H',frame,24,level)
    frame=bytes(frame)
    uc.mem_write(FRAME-16,frame)
    uc.mem_write(STACK-512,b'\x5a'*16);uc.mem_write(STACK+16,b'\x5a'*16)
    # Allocation has completed; its two pending long arguments are still on SP.
    uc.mem_write(STACK-8,struct.pack('>II',1,56))
    for reg,value in ((UC_M68K_REG_A4,CELL),(UC_M68K_REG_A5,A5),(UC_M68K_REG_A6,FRAME),
                      (UC_M68K_REG_A7,STACK-8),(UC_M68K_REG_D6,level)):
        uc.reg_write(reg,value)
    for address,size in ((A5-0x5702,408),(A5-0xb26,4)):
        uc.mem_write(address-16,b'\x5a'*16);uc.mem_write(address+size,b'\x5a'*16)
    draws=[];pending=[];coverage=Counter();copied=[]
    branches=dict(BRANCHES)
    returns=list(RETURN_OFFSETS)
    if factory:
        branches.update({0x4aa6:'type39',0x4ab8:'type63',0x4aca:'type62',
            0x4ae4:'type62_negative',0x4b04:'type62_high',0x4b0c:'type81_141',
            0x4b1e:'type109',0x4b30:'type108',0x4b42:'type100',0x4b54:'type114_116',
            0x4b66:'type25',0x4b76:'type25_low',0x4b84:'type25_middle',
            0x4b92:'type25_other',0x4be4:'type127',0x4c06:'type129',
            0x4c14:'type129_nonzero',0x4c1e:'type129_zero',0x4cc2:'flag24_bit3',
            0x4cca:'byte13',0x4cd2:'flag25_bit2'})
        returns.extend((0x4aae,0x4ac0,0x4ad2,0x4aec,0x4b14,0x4b26,
                        0x4b38,0x4b4a,0x4b5c,0x4bec,0x4c0e))
    if context is not None:
        branches.update({0x4a36:'context_type37',0x4a50:'lookup_nonnegative',
            0x4a56:'lookup_low',0x4a5e:'lookup_lowest',0x4a66:'lookup_high',
            0x4a70:'lookup_middle',0x4a78:'lookup_eligible',0x4a88:'lookup_replacement',
            0x4b9c:'context_type77',0x4ba4:'level_positive',0x4bbc:'level_nonpositive',
            0x4c9e:'context_counter'})
        returns.extend((0x4a3e,0x4a80,0x4a90,0x4cb0))
    def service(machine,address,size,user):
        if address not in allowed:raise AssertionError('unmodeled child-prefix service')
        if address in (A5+0x68a,A5+0x692):
            if pending:raise AssertionError('nested RNG wrapper')
            sp=machine.reg_read(UC_M68K_REG_A7)
            bound=struct.unpack('>H',bytes(machine.mem_read(sp+4,2)))[0]
            pending.append([bound,int(address==A5+0x692)])
        elif not pending:raise AssertionError('helper outside original RNG wrapper')
    def returned(machine,address,size,user):
        if len(pending)!=1:raise AssertionError('unpaired wrapper return')
        draws.append(pending.pop()+[machine.reg_read(UC_M68K_REG_D0)&65535])
    def observe(machine,address,size,user):
        offset=address-BASE
        if offset in branches:coverage[branches[offset]]+=1
        if offset==0x487e:
            if bytes(machine.mem_read(CELL,56))!=c['template']:raise AssertionError('prefix template copy')
            end=machine.reg_read(UC_M68K_REG_A0)
            if end!=TABLE+(selected+1)*56:raise AssertionError('template selection')
            copied.append(selected)
    uc.hook_add(UC_HOOK_CODE,service,begin=A5+32,end=A5+6335)
    for offset in returns:uc.hook_add(UC_HOOK_CODE,returned,begin=BASE+offset,end=BASE+offset)
    for offset in [0x487e,*branches]:uc.hook_add(UC_HOOK_CODE,observe,begin=BASE+offset,end=BASE+offset)
    # Initialization can compile helper blocks; invalidate them after adding hooks.
    uc.ctl_flush_tb()
    stop=0x4cd8 if factory else 0x4974
    uc.emu_start(BASE+0x484e,BASE+stop,count=100000)
    if pending or uc.reg_read(UC_M68K_REG_PC)!=BASE+stop:raise AssertionError('prefix endpoint/draw balance')
    for reg,value in ((UC_M68K_REG_A4,CELL),(UC_M68K_REG_A5,A5),(UC_M68K_REG_A6,FRAME),
                      (UC_M68K_REG_A7,STACK),(UC_M68K_REG_D6,level)):
        if uc.reg_read(reg)!=value:raise AssertionError('prefix register/stack preservation')
    if copied!=[selected]:raise AssertionError('copy boundary count')
    after=bytes(uc.mem_read(CELL-16,88))
    if after[:16]!=b'\xcc'*16 or after[-16:]!=b'\xcc'*16:raise AssertionError('record guards')
    if bytes(uc.mem_read(TABLE-16,len(guarded_table)))!=guarded_table:raise AssertionError('source table changed')
    if bytes(uc.mem_read(A5-0x2626-8,20))!=pointer_context:raise AssertionError('table-pointer context')
    if bytes(uc.mem_read(FRAME-16,len(frame)))!=frame:raise AssertionError('frame changed')
    for address,size in ((A5-0x5702,408),(A5-0xb26,4),(STACK-496,512)):
        if bytes(uc.mem_read(address-16,16))!=b'\x5a'*16 or bytes(uc.mem_read(address+size,16))!=b'\x5a'*16:
            raise AssertionError('RNG/stack guards')
    state=lambda offset:struct.unpack('>I',bytes(uc.mem_read(A5+offset,4)))[0]
    numbers=[state(-0x56fe),state(-0x5702),state(-0xb26),*struct.unpack('>100I',bytes(uc.mem_read(A5-0x56fa,400)))]
    counter_after=None
    if context is not None:
        if bytes(uc.mem_read(A5-0x19af-8,len(lookup_context)))!=lookup_context:raise AssertionError('lookup context changed')
        if bytes(uc.mem_read(0xf0000-16,len(external_context)))!=external_context:raise AssertionError('external template context changed')
        if bytes(uc.mem_read(A5-0x1a48-8,len(external_pointer)))!=external_pointer:raise AssertionError('external pointer context changed')
        counter_after=struct.unpack('>H',bytes(uc.mem_read(A5-0x9f8,2)))[0]
        expected_counter=(context['counter']+int(struct.unpack_from('>H',c['template'])[0] in (137,138)))&65535
        if counter_after!=expected_counter:raise AssertionError('counter mutation')
        expected_context=bytearray(counter_context);struct.pack_into('>H',expected_context,8,expected_counter)
        if bytes(uc.mem_read(A5-0x9f8-8,len(counter_context)))!=bytes(expected_context):raise AssertionError('counter/base context guards')
    line=after[16:-16].hex()+' '+' '.join(map(str,numbers))+f' {selected} {len(draws)}'+''.join(' '+' '.join(map(str,d)) for d in draws)
    if context is not None:line+=' '+str(counter_after)
    return line,len(draws),coverage


def verify(manifest,driver):
    sources={}
    for resource,data in manifest_inputs(manifest,'CODE'):
        sid=resource['id']
        if sid not in SOURCES:continue
        if sid in sources or hashlib.sha256(data).hexdigest()!=SOURCES[sid]:raise ValueError('ambiguous/unsupported CODE source')
        sources[sid]=data
    if set(sources)!=set(SOURCES):raise ValueError('required CODE sources missing')
    inputs=[];wanted=[];count=0;draws=0;max_draws=0;coverage=Counter();digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native output count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:
                aa,bb=a.split(),b.split();token=next((j for j,(x,y) in enumerate(zip(aa,bb)) if x!=y),min(len(aa),len(bb)))
                raise AssertionError(f'child-prefix mismatch case {count-len(wanted)+i}, token {token}')
        inputs.clear();wanted.clear()
    for c in cases():
        line,n,branches=original(sources,c);wanted.append(line);count+=1;draws+=n;max_draws=max(max_draws,n);coverage.update(branches);digest.update((line+'\n').encode())
        inputs.append(' '.join(str(c[k]) for k in ('mode','seed','fallback','last','warmup','variant'))+' '+c['record'].hex()+' '+c['template'].hex()+
                      (' '+' '.join(map(str,c['shuffle'])) if c['mode'] else ''))
        if len(inputs)==128:flush()
    flush()
    if set(coverage)!=set(BRANCHES.values()):raise AssertionError('missing required arithmetic/clamp coverage')
    if max_draws!=8:raise AssertionError('maximum eight-draw path not covered')
    import unicorn
    return {'schema':1,'source_sha256':SOURCES,'unicorn_version':unicorn.__version__,
            'cases':count,'rng_draws':draws,'maximum_draws_per_case':max_draws,'executed_arithmetic_blocks':dict(sorted(coverage.items())),
            'result_sha256':digest.hexdigest(),
            'scope':'CODE 9 supplied-allocation prefix 0x484e..0x4974 over authored 137x56 templates and records; ordered original RNG helpers and complete RNG state compared; allocator, type dispatch, callbacks, later child creation and full gameplay excluded'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} child-prefix cases, {report["rng_draws"]} draws and {len(report["executed_arithmetic_blocks"])} arithmetic/clamp blocks')


if __name__=='__main__':main()

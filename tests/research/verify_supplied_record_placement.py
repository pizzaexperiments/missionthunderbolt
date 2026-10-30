#!/usr/bin/env python3
"""Original supplied factory/follow-up followed by original record attachment."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_finalized_template_factory import ALL_SOURCES,FollowupExecution,cases,BASE7
from verify_record_template_factory import original,TABLE,DESC
from verify_record_factory_tail import CELL
from verify_grid_selector import A5,STACK,STOP
from verify_rng_cpu import manifest_inputs
from unicorn.m68k_const import UC_M68K_REG_A3,UC_M68K_REG_A4,UC_M68K_REG_A5,UC_M68K_REG_A6,UC_M68K_REG_A7,UC_M68K_REG_PC

GRID,SIZE=0x90000,104+19*67*20


class PlacementExecution(FollowupExecution):
    def prepare(self,uc):
        super().prepare(uc)
        c=self.c;world=bytearray(b'\x5a'*SIZE);struct.pack_into('>H',world,18,c['world_count']);struct.pack_into('>I',world,20,c['head'])
        self.slot=104+(c['row']*67+c['column'])*20+12;struct.pack_into('>I',world,self.slot,c['oldlink'])
        self.world=bytes(world);uc.mem_write(GRID-16,b'\xcc'*16+self.world+b'\xcc'*16)
    def inspect(self,uc,observed):
        super().inspect(uc,observed)
        before_rng=bytes(uc.mem_read(A5-0x5702,408))+bytes(uc.mem_read(A5-0xb26,4))
        saved={r:uc.reg_read(r) for r in (UC_M68K_REG_A3,UC_M68K_REG_A4,UC_M68K_REG_A5,UC_M68K_REG_A6)}
        c=self.c;args=struct.pack('>IBBBBI',GRID,c['row'],0xa5,c['column'],0x5a,CELL)
        uc.mem_write(STACK,struct.pack('>I',STOP)+args);uc.reg_write(UC_M68K_REG_A7,STACK)
        uc.emu_start(BASE7+3794,STOP,count=1000)
        if uc.reg_read(UC_M68K_REG_PC)!=STOP or uc.reg_read(UC_M68K_REG_A7)!=STACK+4:raise AssertionError('attachment return/stack')
        if any(uc.reg_read(r)!=v for r,v in saved.items()):raise AssertionError('attachment saved context')
        if bytes(uc.mem_read(A5-0x5702,408))+bytes(uc.mem_read(A5-0xb26,4))!=before_rng:raise AssertionError('attachment changed RNG')
        result=bytes(uc.mem_read(GRID-16,SIZE+32));masked=bytearray(result)
        for p,n in ((18,6),(self.slot,4)):masked[16+p:16+p+n]=self.world[p:p+n]
        if bytes(masked)!=b'\xcc'*16+self.world+b'\xcc'*16:raise AssertionError('unrelated world/guards changed')
        parent=bytes(uc.mem_read(CELL-16,144))
        if parent[:16]!=b'\xcc'*16 or parent[-16:]!=b'\xcc'*16:raise AssertionError('placed record guards')
        self.parent=parent[16:-16];self.header=struct.unpack_from('>HI',result,16+18)
        self.link=struct.unpack_from('>I',result,16+self.slot)[0]
        super().inspect(uc,observed)
        if bytes(uc.mem_read(TABLE-16,len(c['table'])+32))!=b'\x5a'*16+c['table']+b'\x5a'*16:raise AssertionError('placement changed templates')
        if bytes(uc.mem_read(DESC-16,76*12+32))!=b'\x5a'*16+b'\0'*(76*12)+b'\x5a'*16:raise AssertionError('placement changed descriptors')


def verify(manifest,driver):
    sources={r['id']:d for r,d in manifest_inputs(manifest,'CODE') if r['id'] in ALL_SOURCES}
    if set(sources)!=set(ALL_SOURCES) or any(hashlib.sha256(sources[s]).hexdigest()!=h for s,h in ALL_SOURCES.items()):raise ValueError('unsupported CODE')
    inputs=[];wanted=[];count=0;draws=0;callbacks=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        actual=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=30).stdout.splitlines()
        if len(actual)!=len(wanted):raise AssertionError('native count')
        for i,(a,b) in enumerate(zip(actual,wanted)):
            if a!=b:raise AssertionError(f'placement mismatch {count-len(wanted)+i}')
        inputs.clear();wanted.clear()
    for c in cases():
        c['row'],c['column']=[(0,0),(0,66),(1,0),(18,0),(18,66)][count%5]
        c['world_count']=[0,1,32768,65535][count%4];c['head']=[0,CELL,0x11223344][count%3];c['oldlink']=0xdeadbeef
        placement=PlacementExecution(sources,c);line,z,n,f=original(sources,c,followup=placement)
        # Report the actual bytes after attachment; the factory trace/state are
        # retained only after checking attachment left RNG unchanged.
        line=placement.parent.hex()+' '+line.split(' ',1)[1]+f' {placement.header[0]} {placement.header[1]} {placement.link}'
        wanted.append(line);count+=1;draws+=n;callbacks+=f;digest.update((line+'\n').encode())
        keys=('mode','seed','fallback','last','global','warmup','variant')
        text=' '.join(str(c[k]) for k in keys)+f' {c["level"]&65535} {c["flag39"]} '+c['record'].hex()+' '+c['table'].hex()
        text+=' '+b''.join(struct.pack('>h',v) for v in c['thresholds']).hex()+' '+str(len(c['children']))
        text+=f' {c["world_count"]} {c["head"]} {c["row"]} {c["column"]} {c["oldlink"]}'
        text+=''.join(f' {i} '+b.hex() for i,b in sorted(c['children'].items()));inputs.append(text)
        if len(inputs)==16:flush()
    flush()
    import unicorn
    return {'schema':1,'source_sha256':ALL_SOURCES,'unicorn_version':unicorn.__version__,'cases':count,
            'rng_draws':draws,'executed_followups':callbacks,'result_sha256':digest.hexdigest(),
            'scope':'Sequential original supplied factory/follow-up then authored ABI call to original attach; allocator, original glyph caller and child creation excluded'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["cases"]} supplied-record placements with {report["executed_followups"]} original callbacks and {report["rng_draws"]} RNG draws')


if __name__=='__main__':main()

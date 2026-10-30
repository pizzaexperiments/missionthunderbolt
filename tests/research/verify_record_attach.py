#!/usr/bin/env python3
"""Original CODE 7 prepend and composed prepend/unlink on authored records."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_linked_records import PROFILES,machine,call,check_return,GRID

TARGET=0xb0000
SIZE=104+19*67*20


def cases():
    for row in range(19):
        for column in range(67):
            for count in (0,1,32767,32768,65534,65535):
                for head in (0,TARGET,TARGET+0x1000,0xffffffff):
                    yield {'count':count,'head':head,'target':TARGET,'row':row,'column':column,
                           'oldrow':(row+123)&255,'oldcolumn':(column+124)&255,
                           'next':0x12345678,'link':0x89abcdef,'remove':(row+column+count)&1}


def execute(uc,c):
    raw=bytearray(b'\x5a'*(SIZE+32));struct.pack_into('>H',raw,16+18,c['count']);struct.pack_into('>I',raw,16+20,c['head'])
    slot=104+(c['row']*67+c['column'])*20+12
    struct.pack_into('>I',raw,16+slot,c['link']);uc.mem_write(GRID-16,bytes(raw))
    node=bytearray(b'\xa5'*112);node[48]=c['oldrow'];node[49]=c['oldcolumn'];struct.pack_into('>I',node,56,c['next'])
    uc.mem_write(TARGET-16,b'\xcc'*16+bytes(node)+b'\xcc'*16)
    args=struct.pack('>IBBBBI',GRID,c['row'],0xa5,c['column'],0x5a,TARGET)
    call(uc,7,3794,args);check_return(uc)
    if c['remove']:
        call(uc,7,3872,struct.pack('>II',GRID,TARGET));check_return(uc)
    result=bytes(uc.mem_read(GRID-16,SIZE+32));record=bytes(uc.mem_read(TARGET-16,144))
    changed=set(range(16+18,16+24))|set(range(16+slot,16+slot+4))
    if any(a!=b for i,(a,b) in enumerate(zip(result,raw)) if i not in changed):raise AssertionError('unrelated grid/header/guard mutation')
    changed_node={16+48,16+49,*range(16+56,16+60)};original=b'\xcc'*16+bytes(node)+b'\xcc'*16
    if any(a!=b for i,(a,b) in enumerate(zip(record,original)) if i not in changed_node):raise AssertionError('unrelated node/guard mutation')
    values=[struct.unpack_from('>H',result,16+18)[0],struct.unpack_from('>I',result,16+20)[0],
            record[16+48],record[16+49],struct.unpack_from('>I',record,16+56)[0],struct.unpack_from('>I',result,16+slot)[0]]
    return ' '.join(map(str,values))


def verify(manifest,driver):
    from verify_rng_cpu import manifest_inputs
    payloads={r['id']:d for r,d in manifest_inputs(manifest,'CODE') if r['id']==7}
    if set(payloads)!={7} or hashlib.sha256(payloads[7]).hexdigest()!=PROFILES[7]['sha256']:raise ValueError('unsupported CODE 7')
    uc=machine(payloads);inputs=[];wanted=[];count=0;removed=0;digest=hashlib.sha256()
    def flush():
        if not inputs:return
        output=subprocess.run([str(driver.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True,timeout=60).stdout.splitlines()
        if output!=wanted:raise AssertionError(f'attachment mismatch in batch ending at {count}')
        inputs.clear();wanted.clear()
    keys=('count','head','target','row','column','oldrow','oldcolumn','next','link','remove')
    for c in cases():
        line=execute(uc,c);wanted.append(line);digest.update((line+'\n').encode());inputs.append(' '.join(str(c[k]) for k in keys))
        count+=1;removed+=c['remove']
        if len(inputs)==256:flush()
    flush()
    import unicorn
    return {'schema':1,'source_sha256':PROFILES[7]['sha256'],'unicorn_version':unicorn.__version__,
            'attach_cases':count,'composed_unlink_cases':removed,'grid_coordinates':1273,
            'result_sha256':digest.hexdigest(),'scope':'Original CODE 7 attach and head-unlink, authored supplied records; no allocation, creation factory or gameplay semantics'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--native-driver',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();repo=Path(__file__).resolve().parents[2];output=a.output.resolve()
    if output.exists():p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):p.error('keep original evidence private')
    report=verify(a.manifest,a.native_driver);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Matched {report["attach_cases"]} attachment cases including {report["composed_unlink_cases"]} composed removals')


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Validate classic CODE-0 jump-table structure; emit private resource offsets."""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
from pict_catalog import manifest_inputs


def map_jumps(segments):
    data=segments.get(0,b'')
    if len(data)<16:raise ValueError('CODE 0 header missing/truncated')
    above,below,length,a5_offset=struct.unpack_from('>IIII',data)
    if length%8 or length==0 or 16+length>len(data) or a5_offset+length>above:
        raise ValueError('invalid CODE 0 jump-table dimensions')
    entries=[]
    for index,offset in enumerate(range(16,16+length,8)):
        routine,push,segment,load=struct.unpack_from('>HHHH',data,offset)
        if push!=0x3f3c or load!=0xa9f0:raise ValueError('unrecognized unloaded jump stub')
        code=segments.get(segment,b'')
        target=4+routine
        if segment==0 or len(code)<4 or target>=len(code) or target%2:
            raise ValueError('jump target outside segment/alignment')
        entries.append({'index':index,'segment':segment,'resource_offset':target,
                        'a5_displacement':a5_offset+index*8+2,'confidence':'standard-jump-table-structure'})
    counts=Counter(e['segment'] for e in entries)
    for segment,count in counts.items():
        first,number=struct.unpack_from('>HH',segments[segment])
        index=next(e['index'] for e in entries if e['segment']==segment)
        if (first&0x7fff)!=index*8 or number!=count:
            raise ValueError('segment header disagrees with jump-table inventory')
    return {'above_a5_bytes':above,'below_a5_bytes':below,'jump_table_bytes':length,
            'jump_table_a5_offset':a5_offset,'runtime_load_addresses_known':False,'entries':entries}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=a.output.resolve()
    if out.is_relative_to(root) and not out.is_relative_to(root/'local-generated'):p.error('keep outputs private under local-generated/')
    if out.exists():p.error('refusing to overwrite jump-table metadata')
    try:
        records=list(manifest_inputs(a.manifest,'CODE'))
        segments={r['id']:data for r,data in records}
        if len(segments)!=len(records):raise ValueError('ambiguous CODE IDs across source forks')
        mapped=map_jumps(segments);out.mkdir(parents=True)
        (out/'jump-table.json').write_text(json.dumps(mapped,indent=2)+'\n')
        (out/'jump-table.tsv').write_text('segment\tindex\tresource_offset\ta5_displacement\n'+''.join(
            f'{e["segment"]}\t{e["index"]}\t{e["resource_offset"]}\t{e["a5_displacement"]}\n' for e in mapped['entries']))
    except (ValueError,OSError,KeyError) as e:p.error(str(e))
    print(f'Validated {len(mapped["entries"])} unloaded jump entries; no runtime addresses or game symbols inferred')

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Prepare private, hash-verified CODE/CREL files without inventing load addresses."""
import argparse
import json
from pathlib import Path
from pict_catalog import manifest_inputs


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=a.output.resolve()
    if out.is_relative_to(root) and not out.is_relative_to(root/'local-generated'):p.error('output must remain local-generated/ or outside checkout')
    if out.exists():p.error('refusing to overwrite segments')
    try:
        rows=[];files=[]
        for typ in ('CODE','CREL'):
            for i,(record,data) in enumerate(manifest_inputs(a.manifest,typ)):
                name=f'{typ}_{record["id"]}_{i:03d}.bin'
                rows.append({'type':typ,'id':record['id'],'fork':record['fork'],'sha256':record['sha256'],
                             'bytes':len(data),'output':name,'import_base':0,'runtime_load_address':None})
                files.append((name,data))
        if not rows:raise ValueError('no CODE/CREL segments')
        out.mkdir(parents=True)
        for name,data in files:(out/name).write_bytes(data)
        (out/'segments.json').write_text(json.dumps({'schema':1,'segments':rows},indent=2)+'\n')
    except (ValueError,OSError,KeyError) as e:p.error(str(e))
    print(f'Prepared {len(rows)} private segments; base zero denotes resource offsets, not runtime addresses')

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Validate provenance and evidence labels in a manually captured reference trace."""
import argparse
import json
from pathlib import Path
import re


def validate(trace):
    if trace.get('schema') != 1: raise ValueError('unsupported trace schema')
    for key in ('run_id','game_version','environment'):
        if not isinstance(trace.get(key),str) or not trace[key].strip(): raise ValueError(f'missing {key}')
    if not re.fullmatch('[0-9a-f]{64}',trace.get('source_sha256','')): raise ValueError('invalid source SHA256')
    events=trace.get('events')
    if not isinstance(events,list) or not events: raise ValueError('trace requires events')
    for index,event in enumerate(events):
        if event.get('step')!=index: raise ValueError('steps must start at zero and be contiguous')
        if not isinstance(event.get('action'),str) or not event['action'].strip(): raise ValueError('missing action')
        if event.get('confidence') not in ('observed','hypothesis','unknown'): raise ValueError('invalid confidence')
        if not isinstance(event.get('state'),dict): raise ValueError('state must be an object')
        evidence=event.get('evidence')
        if not isinstance(evidence,list) or any(not isinstance(e,str) or not e.strip() for e in evidence):
            raise ValueError('evidence must be a list of nonempty references')
        if event['confidence']=='observed' and not evidence: raise ValueError('observed event requires evidence')
    return len(events)


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('trace',type=Path); args=parser.parse_args()
    try: count=validate(json.loads(args.trace.read_text()))
    except (ValueError,KeyError,TypeError,OSError) as e: parser.error(str(e))
    print(f'Validated {count} labeled events; schema validation does not verify historical accuracy')

if __name__=='__main__':main()

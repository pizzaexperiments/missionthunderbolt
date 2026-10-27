#!/usr/bin/env python3
"""Index externally supplied Macintosh A-line constants; keep references private."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

PATTERN=re.compile(r'^\s*(_[A-Za-z][A-Za-z0-9_]*)\s*=\s*(0x[Aa][0-9A-Fa-f]{3})\s*[,}]',re.MULTILINE)


def parse_constants(data):
    aliases=defaultdict(set)
    for name,number in PATTERN.findall(data.decode('latin-1')):
        aliases[int(number,16)].add(name)
    if not aliases:raise ValueError('no supported A-line enum constants found')
    return [{'word':word,'hex':f'0x{word:04x}','names':sorted(names)} for word,names in sorted(aliases.items())]


def prepare(source,output,reference_url=None):
    repo=Path(__file__).resolve().parents[1];output=output.resolve()
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):
        raise ValueError('keep third-party reference outputs under local-generated/ or outside checkout')
    if output.exists():raise ValueError('refusing to overwrite reference output')
    data=source.read_bytes();traps=parse_constants(data)
    document={'schema':1,'source':source.name,'source_sha256':hashlib.sha256(data).hexdigest(),
              'reference_url':reference_url,'matching':'exact word only; no OS/version/patch semantics inferred',
              'traps':traps}
    output.mkdir(parents=True)
    (output/'trap-reference.json').write_text(json.dumps(document,indent=2)+'\n')
    (output/'trap-reference.tsv').write_text('word\tnames\n'+''.join(f'{row["word"]}\t{";".join(row["names"])}\n' for row in traps))
    return document


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--reference-url');a=p.parse_args()
    try:document=prepare(a.source,a.output,a.reference_url)
    except (ValueError,OSError) as error:p.error(str(error))
    print(f'Indexed {len(document["traps"])} exact trap words; reference and reports remain private')

if __name__=='__main__':main()

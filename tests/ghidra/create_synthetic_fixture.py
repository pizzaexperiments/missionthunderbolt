#!/usr/bin/env python3
"""Create an authored 68000 control-flow fixture, without any game bytes/headers."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];out=a.output.resolve()
if out.exists():p.error('refusing to overwrite fixture output')
if out.is_relative_to(root) and not out.is_relative_to(root/'local-generated'):p.error('use ignored local-generated/ or an external directory')
# LINK A6,0; a synthetic A-line word; UNLK A6; RTS. Not extracted from the game.
data=bytes.fromhex('4e560000a9a04e5e4e75')
out.mkdir(parents=True)
(out/'CODE_99_000.bin').write_bytes(data)
(out/'trap-reference.tsv').write_text('word\tnames\n43424\t_SyntheticResource\n')
(out/'fixture.json').write_text(json.dumps({'kind':'synthetic-authored','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()},indent=2)+'\n')

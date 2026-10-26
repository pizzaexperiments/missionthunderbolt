#!/usr/bin/env python3
"""Convert supported uncompressed Macintosh snd resources to local PCM WAV."""
import argparse
import io
import json
from pathlib import Path
import struct
import wave
from pict_catalog import manifest_inputs, Unsupported


def decode_sound(data):
    def u16(offset):
        if offset<0 or offset+2>len(data): raise ValueError('truncated snd header')
        return struct.unpack_from('>H',data,offset)[0]
    fmt=u16(0)
    if fmt==1:
        modifiers=u16(2)
        if modifiers>16 or 4+modifiers*6+2>len(data): raise ValueError('invalid snd modifiers')
        for i in range(modifiers):
            if u16(4+i*6)!=5: raise Unsupported('non-sampled sound synthesizer')
        offset=4+modifiers*6
    elif fmt==2: offset=4; u16(2)
    else: raise Unsupported(f'unsupported snd format {fmt}')
    commands=u16(offset); table=offset+2
    if not 1<=commands<=1024 or table+commands*8>len(data): raise ValueError('invalid snd commands')
    buffers=[]
    for i in range(commands):
        cmd,param1,param2=struct.unpack_from('>HHI',data,table+i*8)
        if cmd in (0x8050,0x8051):buffers.append(param2)
        elif cmd!=0:raise Unsupported(f'unsupported snd command 0x{cmd:04x}')
    if len(buffers)!=1: raise Unsupported('requires exactly one offset-based sound buffer')
    start=buffers[0]
    if start<table+commands*8 or start+22>len(data): raise ValueError('invalid sound buffer offset')
    pointer,length,rate_fixed,loop_start,loop_end,encoding,base=struct.unpack_from('>IIIII BB',data,start)
    if pointer!=0: raise Unsupported('external sample pointer')
    channels,bits=1,8
    if encoding==0: frames=length; pcm_start=start+22
    elif encoding==0xff:
        if start+64>len(data):raise ValueError('truncated extended sound header')
        channels=length;frames=struct.unpack_from('>I',data,start+22)[0];bits=u16(start+48);pcm_start=start+64
        if channels not in (1,2) or bits not in (8,16): raise Unsupported('unsupported extended PCM layout')
    else: raise Unsupported(f'compressed/unsupported sound encoding 0x{encoding:02x}')
    rate=round(rate_fixed/65536)
    if not 1<=rate<=192000 or frames>16*1024*1024: raise ValueError('invalid sound dimensions/rate')
    size=frames*channels*(bits//8)
    if pcm_start+size>len(data):raise ValueError('truncated PCM samples')
    if not 0<=loop_start<=loop_end<=frames:raise ValueError('invalid loop bounds')
    samples=data[pcm_start:pcm_start+size]
    if bits==16: samples=b''.join(samples[i:i+2][::-1] for i in range(0,len(samples),2))
    stream=io.BytesIO()
    with wave.open(stream,'wb') as wav:
        wav.setnchannels(channels);wav.setsampwidth(bits//8);wav.setframerate(rate);wav.writeframes(samples)
    return stream.getvalue(),{'channels':channels,'sample_bits':bits,'frames':frames,'sample_rate':rate,
                             'source_rate_fixed':rate_fixed,'loop_start':loop_start,'loop_end':loop_end,
                             'base_frequency':base}


def catalog(manifest,output):
    if output.exists():raise ValueError('refusing to overwrite output directory')
    inputs=list(manifest_inputs(manifest,'snd '))
    if not inputs:raise ValueError('manifest has no snd resources')
    repo=Path(__file__).resolve().parents[1]; resolved=output.resolve()
    if resolved.is_relative_to(repo) and not resolved.is_relative_to(repo/'local-generated'):
        raise ValueError('outputs inside checkout must stay under local-generated/')
    output.mkdir(parents=True);report=[]
    for index,(record,data) in enumerate(inputs):
        row={'fork':record['fork'],'id':record['id'],'sha256':record['sha256']}
        try:
            wav,metadata=decode_sound(data); name=f'{index:04d}_snd_{record["id"]}.wav'
            (output/name).write_bytes(wav);row.update(status='converted',output=name,**metadata)
        except (Unsupported,ValueError) as e:
            row.update(status='unsupported' if isinstance(e,Unsupported) else 'malformed',reason=str(e))
        report.append(row)
    (output/'report.json').write_text(json.dumps({'schema':1,'resources':report},indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:report=catalog(a.manifest,a.output)
    except (ValueError,OSError,KeyError) as e:p.error(str(e))
    counts={s:sum(r['status']==s for r in report) for s in ('converted','unsupported','malformed')}
    print(json.dumps(counts));return 0 if counts['converted']==len(report) else 2

if __name__=='__main__':raise SystemExit(main())

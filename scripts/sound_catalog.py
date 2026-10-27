#!/usr/bin/env python3
"""Convert supported uncompressed Macintosh snd resources to local PCM WAV."""
import argparse
import io
import json
from pathlib import Path
import struct
import wave
from pict_catalog import manifest_inputs, Unsupported


COMMAND_NAMES={0:'nullCmd',40:'freqDurationCmd',41:'restCmd',80:'soundCmd',81:'bufferCmd'}


def inspect_commands(data):
    """Validate command-list structure; preserve parameters without rendering a schedule."""
    def u16(offset):
        if offset<0 or offset+2>len(data): raise ValueError('truncated snd header')
        return struct.unpack_from('>H',data,offset)[0]
    fmt=u16(0);modifiers=[]
    if fmt==1:
        count=u16(2)
        if count>16 or 4+count*6+2>len(data): raise ValueError('invalid snd modifiers')
        for i in range(count):
            identifier,initialization=struct.unpack_from('>HI',data,4+i*6)
            modifiers.append({'synthesizer':identifier,'initialization':initialization})
        offset=4+count*6
    elif fmt==2: offset=4; u16(2)
    else: raise Unsupported(f'unsupported snd format {fmt}')
    count=u16(offset);table=offset+2
    if not 1<=count<=1024 or table+count*8>len(data): raise ValueError('invalid snd commands')
    commands=[]
    for i in range(count):
        cmd,param1,param2=struct.unpack_from('>HhI',data,table+i*8)
        number=cmd&0x7fff
        commands.append({'index':i,'word':cmd,'command':number,
                         'name':COMMAND_NAMES.get(number,'unknown'),
                         'data_offset':bool(cmd&0x8000),'param1':param1,'param2':param2})
    return {'format':fmt,'modifiers':modifiers,'commands':commands,'table_end':table+count*8}


def decode_sound(data,sample_only=False):
    listing=inspect_commands(data)
    if any(m['synthesizer']!=5 for m in listing['modifiers']):
        raise Unsupported('non-sampled sound synthesizer')
    buffers=[];sequence=False
    for command in listing['commands']:
        cmd=command['word']
        if cmd in (0x8050,0x8051):buffers.append(command['param2'])
        elif cmd!=0:
            if not sample_only or cmd not in (40,41):raise Unsupported(f'unsupported snd command 0x{cmd:04x}')
            sequence=True
    if len(buffers)!=1: raise Unsupported('requires exactly one offset-based sound buffer')
    start=buffers[0]
    if start<listing['table_end'] or start+22>len(data): raise ValueError('invalid sound buffer offset')
    def u16(offset):
        if offset<0 or offset+2>len(data):raise ValueError('truncated sound header')
        return struct.unpack_from('>H',data,offset)[0]
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
                             'base_frequency':base,'playback_scope':'sample-only' if sequence else 'single-buffer'}


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
            row['command_list']=inspect_commands(data)
            wav,metadata=decode_sound(data,sample_only=True); name=f'{index:04d}_snd_{record["id"]}.wav'
            (output/name).write_bytes(wav);row.update(status='sample-only' if metadata['playback_scope']=='sample-only' else 'converted',output=name,**metadata)
        except (Unsupported,ValueError) as e:
            row.update(status='unsupported' if isinstance(e,Unsupported) else 'malformed',reason=str(e))
        report.append(row)
    (output/'report.json').write_text(json.dumps({'schema':1,'resources':report},indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:report=catalog(a.manifest,a.output)
    except (ValueError,OSError,KeyError) as e:p.error(str(e))
    counts={s:sum(r['status']==s for r in report) for s in ('converted','sample-only','unsupported','malformed')}
    print(json.dumps(counts));return 0 if counts['converted']==len(report) else 2

if __name__=='__main__':raise SystemExit(main())

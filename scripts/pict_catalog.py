#!/usr/bin/env python3
"""Strict indexed-raster PICT decoder and local PNG catalog (no vector guesses)."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

MAX_PIXELS = 4_194_304

class Unsupported(ValueError):
    pass

class Reader:
    def __init__(self, data): self.data, self.pos = data, 0
    def read(self, n):
        if n < 0 or self.pos + n > len(self.data): raise ValueError('truncated PICT')
        value = self.data[self.pos:self.pos+n]; self.pos += n; return value
    def u16(self): return struct.unpack('>H', self.read(2))[0]
    def rect(self):
        top,left,bottom,right=struct.unpack('>hhhh',self.read(8))
        if bottom <= top or right <= left: raise ValueError('invalid PICT rectangle')
        return top,left,bottom,right


def unpackbits(data, expected):
    out=bytearray(); r=Reader(data)
    while r.pos < len(data):
        control=r.read(1)[0]
        if control < 128: out.extend(r.read(control+1))
        elif control > 128: out.extend(r.read(1)*(257-control))
        if len(out)>expected: raise ValueError('PackBits row overflow')
    if len(out)!=expected: raise ValueError('PackBits row length mismatch')
    return bytes(out)


def decode(data):
    r=Reader(data); r.read(2); frame=r.rect()
    top,left,bottom,right=frame; width,height=right-left,bottom-top
    if width*height > MAX_PIXELS: raise ValueError('PICT exceeds pixel limit')
    pixels=bytearray(b'\xff\xff\xff'*(width*height)); clip=frame
    version=r.read(2)
    if version==b'\x00\x11':
        if r.read(2)!=b'\x02\xff': raise Unsupported('unsupported PICT version')
        word=True
    elif version==b'\x11\x01': word=False
    else: raise Unsupported('unsupported PICT version')
    painted=False
    while r.pos < len(data):
        if word and r.pos%2: r.read(1)
        op=r.u16() if word else r.read(1)[0]
        if op==0xff:
            if not painted: raise Unsupported('no supported raster drawing found')
            return width,height,bytes(pixels)
        if op in (0,0x1e): continue
        if op==0xa0: r.read(2); continue
        if op==0xa1:
            r.read(2); size=r.u16(); r.read(size); continue
        if op==0x0c00 and word: r.read(24); continue
        if op==1:
            if r.u16()!=10: raise Unsupported('nonrectangular clipping region')
            clip=r.rect(); continue
        if op not in (0x90,0x98): raise Unsupported(f'unsupported PICT opcode 0x{op:04x}')
        row_field=r.u16(); row_bytes=row_field&0x3fff; bounds=r.rect()
        bt,bl,bb,br=bounds; bw,bh=br-bl,bb-bt
        if bw*bh>MAX_PIXELS or row_bytes==0: raise ValueError('invalid raster size')
        palette={0:(255,255,255),1:(0,0,0)}; depth=1; pack_type=0
        if row_field&0x8000:
            pm=struct.unpack('>HHIIIHHHHIII',r.read(36))
            _,pack_type,_,_,_,pixel_type,depth,components,component_bits,_,_,_=pm
            if pixel_type!=0 or depth not in (1,4,8) or components!=1 or component_bits!=depth:
                raise Unsupported('only indexed 1/4/8-bit PixMaps are supported')
            if pack_type not in (0,1): raise Unsupported('unsupported PixMap packing type')
            r.read(4); flags=r.u16(); colors=r.u16()+1
            if colors>256: raise ValueError('oversized palette')
            palette={}
            for ordinal in range(colors):
                index,red,green,blue=struct.unpack('>HHHH',r.read(8))
                index=ordinal if flags&0x8000 else index
                if index in palette or index >= 1<<depth: raise ValueError('invalid palette index')
                palette[index]=(red>>8,green>>8,blue>>8)
        if row_bytes < (bw*depth+7)//8 or row_bytes > 32768 or row_bytes*bh > 32*1024*1024:
            raise ValueError('invalid raster stride')
        src=r.rect(); dst=r.rect(); mode=r.u16()
        if mode!=0: raise Unsupported('only srcCopy transfer mode is supported')
        st,sl,sb,sr=src; dt,dl,db,dr=dst
        if st<bt or sl<bl or sb>bb or sr>br: raise ValueError('source rectangle outside raster')
        rows=[]
        for _ in range(bh):
            if op==0x98 and row_bytes>=8 and pack_type!=1:
                n=r.u16() if row_bytes>250 else r.read(1)[0]
                row=unpackbits(r.read(n),row_bytes)
            else: row=r.read(row_bytes)
            rows.append(row)
        ct,cl,cb,cr=clip
        for y in range(max(top,dt,ct),min(bottom,db,cb)):
            sy=st+(y-dt)*(sb-st)//(db-dt)-bt
            for x in range(max(left,dl,cl),min(right,dr,cr)):
                sx=sl+(x-dl)*(sr-sl)//(dr-dl)-bl
                bit=sx*depth; index=(rows[sy][bit//8]>>(8-depth-bit%8))&((1<<depth)-1)
                if index not in palette: raise ValueError('pixel references absent palette entry')
                offset=((y-top)*width+x-left)*3
                pixels[offset:offset+3]=bytes(palette[index])
        painted=True
    raise ValueError('missing EndPic')


def png(width,height,pixels):
    if width*height>MAX_PIXELS or len(pixels)!=width*height*3: raise ValueError('invalid PNG dimensions')
    def chunk(kind,body):
        return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
    raw=b''.join(b'\0'+pixels[y*width*3:(y+1)*width*3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))
            +chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


def manifest_inputs(manifest, resource_type):
    root=manifest.resolve().parent; document=json.loads(manifest.read_text())
    if document.get('schema')!=1: raise ValueError('unsupported extraction manifest schema')
    for record in document['resources']:
        if record['type']!=resource_type: continue
        path=(root/record['output']).resolve()
        if not path.is_relative_to(root): raise ValueError('manifest payload escapes extraction directory')
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=record['sha256']: raise ValueError('resource checksum mismatch')
        yield record,data


def catalog(manifest, output):
    if output.exists(): raise ValueError('refusing to overwrite catalog')
    inputs=list(manifest_inputs(manifest,'PICT'))
    if not inputs: raise ValueError('manifest contains no PICT resources')
    repo=Path(__file__).resolve().parents[1]; resolved=output.resolve()
    if resolved.is_relative_to(repo) and not resolved.is_relative_to(repo/'local-generated'):
        raise ValueError('catalog must remain under local-generated/ or outside checkout')
    output.mkdir(parents=True); report=[]; images=[]
    for i,(record,data) in enumerate(inputs):
        row={'fork':record['fork'],'id':record['id'],'sha256':record['sha256']}
        try:
            w,h,pixels=decode(data); name=f'{i:04d}_PICT_{record["id"]}.png'
            (output/name).write_bytes(png(w,h,pixels))
            row.update(status='decoded',width=w,height=h,output=name,cell=len(images)); images.append((w,h,pixels))
        except (Unsupported,ValueError) as e:
            row.update(status='unsupported' if isinstance(e,Unsupported) else 'malformed',reason=str(e))
        report.append(row)
    if images:
        # Bounded sheets: 128 images/page, stable cells linked by resource ID.
        cell=128
        for page,begin in enumerate(range(0,len(images),128)):
            group=images[begin:begin+128]; cols=min(8,len(group)); rows=(len(group)+cols-1)//cols
            sheet=bytearray(b'\xcc\xcc\xcc'*(cell*cell*cols*rows)); sw=cols*cell
            for i,(w,h,pixels) in enumerate(group):
                scale=min(cell/w,cell/h,1); tw,th=max(1,int(w*scale)),max(1,int(h*scale))
                for y in range(th):
                    for x in range(tw):
                        src=((y*h//th)*w+x*w//tw)*3; dst=(((i//cols)*cell+y)*sw+(i%cols)*cell+x)*3
                        sheet[dst:dst+3]=pixels[src:src+3]
            name='contact-sheet.png' if page==0 else f'contact-sheet-{page:03d}.png'
            (output/name).write_bytes(png(sw,rows*cell,bytes(sheet)))
        for row in report:
            if row['status']=='decoded':
                index=row['cell']; row['sheet']=index//128; row['cell']=index%128
    (output/'report.json').write_text(json.dumps({'schema':1,'resources':report},indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('manifest',type=Path); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    try: report=catalog(a.manifest,a.output)
    except (ValueError,OSError,KeyError) as e: p.error(str(e))
    counts={s:sum(r['status']==s for r in report) for s in ('decoded','unsupported','malformed')}
    print(json.dumps(counts)); return 0 if counts['decoded']==len(report) else 2

if __name__=='__main__': raise SystemExit(main())

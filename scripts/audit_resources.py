#!/usr/bin/env python3
"""Metadata-only classic Macintosh resource-fork auditor. No proprietary bytes emitted."""
import argparse,csv,hashlib,pathlib,struct
def u16(b,i):
    if i<0 or i+2>len(b): raise ValueError("truncated u16")
    return struct.unpack_from(">H",b,i)[0]
def u32(b,i):
    if i<0 or i+4>len(b): raise ValueError("truncated u32")
    return struct.unpack_from(">I",b,i)[0]
def parse_fork(b):
    if len(b)<16: raise ValueError("truncated header")
    d,m,dl,ml=struct.unpack_from(">IIII",b)
    if d+dl>len(b) or m+ml>len(b) or ml<30: raise ValueError("invalid sections")
    end=m+ml
    tl=m+u16(b,m+24)
    if tl+2>end: raise ValueError("invalid type list")
    n=u16(b,tl)+1
    if tl+2+8*n>end: raise ValueError("invalid type entries")
    for i in range(n):
        t=tl+2+i*8
        typ=b[t:t+4].decode("mac_roman")
        count=u16(b,t+4)+1
        refs=tl+u16(b,t+6)
        if refs+12*count>end: raise ValueError("invalid references")
        for j in range(count):
            r=refs+j*12
            rid=struct.unpack_from(">h",b,r)[0]
            off=int.from_bytes(b[r+5:r+8],"big")
            a=d+off
            if a+4>d+dl: raise ValueError("resource offset out of bounds")
            size=u32(b,a)
            if a+4+size>d+dl: raise ValueError("resource data out of bounds")
            payload=b[a+4:a+4+size]
            w=h=""
            if typ=="PICT" and len(payload)>=10:
                top,left,bottom,right=struct.unpack_from(">hhhh",payload,2)
                w,h=right-left,bottom-top
            yield (typ,rid,size,w,h,hashlib.sha256(payload).hexdigest())
def main():
    p=argparse.ArgumentParser()
    p.add_argument("resource_dir",type=pathlib.Path)
    p.add_argument("--output",type=pathlib.Path,required=True)
    a=p.parse_args()
    if not a.resource_dir.is_dir(): p.error("resource_dir missing")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("w",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["fork","type","id","bytes","pict_width","pict_height","sha256"])
        count=0
        for path in sorted(a.resource_dir.rglob("*.rsrc")):
            for typ,rid,size,w,h,sha in parse_fork(path.read_bytes()):
                writer.writerow([str(path.relative_to(a.resource_dir)),typ,rid,size,w,h,sha])
                count+=1
    print("Audited",count,"resources")
if __name__=="__main__": main()

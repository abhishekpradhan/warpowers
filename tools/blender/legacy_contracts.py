"""Ownership panels for the retained original base kit, applied after export."""
from pathlib import Path
import sys,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from genw3d import mesh_chunk,frustum,name32
from w3dhierarchy import chunks,chunk

PANELS={
 'mercc01':(-2,-5,28.46,4.2,4.2,.10),
 'jakcp01':(-3,0,12.27,4.5,4.5,.10),
 'merpp01':(-2,0,14.12,4.5,5,.10),
 'merwf01':(21,-6,10.36,4.5,5,.10),
 'jakcs01':(0,0,16.67,7,2,.10),
 'mersuv01':(-1.8,0,8.36,2.1,2.7,.10),
 'jakrig01':(5,0,6.76,2.4,2.8,.10),
}

def apply(path):
    path=Path(path);model=path.stem.lower()
    if model not in PANELS:return
    # Reruns are idempotent. Older base models bind everything to the root.
    data=path.read_bytes();name='HOUSECOLOR0';out=b''
    for c,s,p in chunks(data):
        if c==0:
            header=next(q for d,t,q in chunks(p) if d==0x1f)
            if header[8:24].split(b'\0')[0].startswith(b'HOUSECOLOR'):continue
        if c==0x700:
            out+=mesh_chunk(model.upper(),name,(220,220,220),frustum(*PANELS[model]))
            inner=b''
            for d,t,q in chunks(p):
                if d==0x702:
                    entries=[(e,u,r) for e,u,r in chunks(q) if e!=0x704 or b'.HOUSECOLOR' not in r]
                    entries.append((0x704,False,struct.pack('<I32s',0,name32(model.upper()+'.'+name))))
                    count=sum(e==0x704 for e,u,r in entries)
                    q=b''.join(chunk(e,u,struct.pack('<I',count)+r[4:] if e==0x703 else r) for e,u,r in entries)
                inner+=chunk(d,t,q)
            p=inner
        out+=chunk(c,s,p)
    path.write_bytes(out)

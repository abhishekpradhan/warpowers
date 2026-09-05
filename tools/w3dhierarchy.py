"""Canonical W3D pivot ordering and HLOD index remapping.

The native hierarchy and Blender importer both need parents before children.
Only reorder embedded hierarchies; shared infantry rigs keep their own contract.
"""
import struct


def chunks(data):
    pos=0
    while pos<len(data):
        kind,size=struct.unpack_from('<II',data,pos)
        end=pos+8+(size&0x7fffffff)
        if end>len(data):raise ValueError('Truncated W3D chunk')
        yield kind,bool(size&0x80000000),data[pos+8:end]
        pos=end


def chunk(kind,sub,payload):
    return struct.pack('<II',kind,len(payload)|(0x80000000 if sub else 0))+payload


def canonicalize(data):
    hierarchy=next((p for c,s,p in chunks(data) if c==0x100),None)
    if hierarchy is None:return data
    pivotdata=next(p for c,s,p in chunks(hierarchy) if c==0x102)
    pivots=[pivotdata[i:i+60] for i in range(0,len(pivotdata),60)]
    parents=[struct.unpack_from('<I',p,16)[0] for p in pivots]
    order=[];pending=list(range(len(pivots)))
    while pending:
        ready=[i for i in pending if parents[i]==0xffffffff or parents[i] in order]
        if not ready:raise ValueError('Cyclic or missing W3D pivot parent')
        order.extend(ready);pending=[i for i in pending if i not in ready]
    remap={old:new for new,old in enumerate(order)}
    updated=b''.join(pivots[i][:16]+struct.pack('<I',remap.get(parents[i],0xffffffff))+pivots[i][20:] for i in order)
    result=b''
    for c,s,p in chunks(data):
        if c==0x100:p=b''.join(chunk(d,t,updated if d==0x102 else q) for d,t,q in chunks(p))
        if c==0x700:
            inner=b''
            for d,t,q in chunks(p):
                if d==0x702:
                    q=b''.join(chunk(e,u,struct.pack('<I',remap[struct.unpack_from('<I',r)[0]])+r[4:] if e==0x704 else r)
                               for e,u,r in chunks(q))
                inner+=chunk(d,t,q)
            p=inner
        result+=chunk(c,s,p)
    return result

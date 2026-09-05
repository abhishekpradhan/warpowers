#!/usr/bin/env python3
"""Generate tactical overview art from the actual generated .map data.

python3 tools/gentactical.py --data data
Reads terrain heights, placed props, resources and deployment positions; no
separate hand-maintained battlefield diagram can drift from the playable map.
"""
import argparse
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]
MAPS=[('Flats','WPTest'),('Ridge','WPRidge'),('Scrap','WPScrap'),('Basin','WPBasin'),('Range','WPRange')]

def read_map(path):
    data=path.read_bytes()
    if data[:4]!=b'CkMp':raise ValueError(f'Unsupported map {path}')
    count=struct.unpack_from('<I',data,4)[0];p=8;toc={}
    for _ in range(count):
        n=data[p];p+=1;name=data[p:p+n].decode();p+=n
        key=struct.unpack_from('<I',data,p)[0];p+=4;toc[key]=name
    def chunks(data,start=0):
        while start<len(data):
            key,version,size=struct.unpack_from('<IHi',data,start);start+=10
            yield toc[key],data[start:start+size];start+=size
    top=dict(chunks(data,p));h=top['HeightMapData']
    w,height,border,n=struct.unpack_from('<4i',h)
    start=16+n*8+4;heights=h[start:start+w*height]
    objects=[]
    for typ,payload in chunks(top['ObjectsList']):
        x,y=struct.unpack_from('<ff',payload);p=20
        n=struct.unpack_from('<H',payload,p)[0];p+=2;name=payload[p:p+n].decode();p+=n
        pairs=struct.unpack_from('<H',payload,p)[0];p+=2;props={}
        for _ in range(pairs):
            tag=struct.unpack_from('<I',payload,p)[0];p+=4;t=tag&255;key=toc[tag>>8]
            if t==0:value=payload[p];p+=1
            elif t in (1,2):value=struct.unpack_from('<i' if t==1 else '<f',payload,p)[0];p+=4
            elif t in (3,4):
                n=struct.unpack_from('<H',payload,p)[0];p+=2
                size=n*(2 if t==4 else 1);value=payload[p:p+size].decode('utf-16-le' if t==4 else 'ascii');p+=size
            else:raise ValueError(f'Unknown map property type {t}')
            props[key]=value
        objects.append((x,y,name,props))
    return w,height,border,heights,objects

def preview(path,ash=False):
    w,h,border,heights,objects=read_map(path);play=w-2*border;extent=play*10
    pw,ph=256,192;out=[[(19,26,28)]*pw for _ in range(ph)]
    size=172;ox=(pw-size)//2;oy=10
    def height(x,y):return heights[max(0,min(h-1,y))*w+max(0,min(w-1,x))]
    for y in range(size):
        cy=border+round((size-1-y)/(size-1)*(play-1))
        for x in range(size):
            cx=border+round(x/(size-1)*(play-1));z=height(cx,cy)
            slope=(height(cx-1,cy)-height(cx+1,cy))*.022+(height(cx,cy-1)-height(cx,cy+1))*.017
            light=max(.48,min(1.45,.86+slope+(z-16)*.006))
            base=(94,106,104) if ash else (123,112,82)
            if z>32:base=(105,107,94) if ash else (148,128,88)
            if z<13:base=(79,92,86)
            grid=(x%34==0 or y%34==0)
            out[y+oy][x+ox]=tuple(round(min(255,c*light+(7 if grid else 0))) for c in base)
    def pixel(x,y,c):
        if 0<=x<pw and 0<=y<ph:out[y][x]=c
    def square(x,y,r,c):
        for yy in range(y-r,y+r+1):
            for xx in range(x-r,x+r+1):pixel(xx,yy,c)
    def ring(x,y,r,c):
        for yy in range(y-r,y+r+1):
            for xx in range(x-r,x+r+1):
                d=(xx-x)**2+(yy-y)**2
                if (r-1)**2<=d<=r*r:pixel(xx,yy,c)
    for x,y,name,props in objects:
        sx=ox+round(x/extent*(size-1));sy=oy+size-1-round(y/extent*(size-1))
        if name.startswith('*'):continue
        owner=str(props.get('originalOwner',''))
        if 'SupplyCache' in name:
            square(sx,sy,3,(28,44,41));square(sx,sy,2,(109,175,149));continue
        if name.startswith('WP_Prop'):
            r=2 if 'Rock' in name else 1;square(sx,sy,r,(59,67,63));continue
        friendly='PlayerA' in owner
        tint=(228,185,85) if friendly else (196,107,87)
        if 'Command' in name:
            ring(sx,sy,9,tint);square(sx,sy,4,(24,31,32));square(sx,sy,2,tint)
        elif 'Relay' in name:
            ring(sx,sy,6,(128,184,180));square(sx,sy,2,(190,218,204))
        else:square(sx,sy,1,tint)
    for x in range(ox-1,ox+size+1):pixel(x,oy-1,(131,143,132));pixel(x,oy+size,(66,84,84))
    for y in range(oy,oy+size):pixel(ox-1,y,(98,111,106));pixel(ox+size,y,(66,84,84))
    # Four compass tick marks and a north point, without raster lettering.
    for d in range(6):pixel(pw//2,2+d,(214,177,88))
    pixel(pw//2-1,4,(214,177,88));pixel(pw//2+1,4,(214,177,88))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=ROOT/'data');args=ap.parse_args()
    w,h=1024,512;atlas=[[(19,26,28)]*w for _ in range(h)];ini=['; Tactical previews generated from actual maps by tools/gentactical.py.']
    for i,(label,name) in enumerate(MAPS):
        p=preview(args.data/'Maps'/name/(name+'.map'),label in ('Scrap','Range'))
        bx=(i%4)*256;by=(i//4)*192
        for y,row in enumerate(p):atlas[by+y][bx:bx+256]=row
        ini.append(f'\nMappedImage WPMapPreview{label}\n  Texture = wp_map_previews.tga\n  TextureWidth = {w}\n  TextureHeight = {h}\n  Coords = Left:{bx} Top:{by} Right:{bx+256} Bottom:{by+192}\n  Status = NONE\nEnd')
    header=bytearray(18);header[2]=2;header[16]=24;header[17]=32;struct.pack_into('<HH',header,12,w,h)
    (args.data/'Art/Textures/wp_map_previews.tga').write_bytes(header+bytes(c for row in atlas for r,g,b in row for c in (b,g,r)))
    (args.data/'Data/INI/MappedImages/HandCreated/WPMapPreviews.ini').write_text('\n'.join(ini)+'\n')
    print('TACTICAL_PREVIEWS_OK',len(MAPS))

if __name__=='__main__':main()

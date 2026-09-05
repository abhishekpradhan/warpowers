#!/usr/bin/env python3
"""Lossless TGA storage optimization plus camera-appropriate small-unit atlases.

python3 tools/optimize_art.py --data data
Every image keeps its exact dimensions/pixels except explicitly named atlases
authored at256px or128px (older exports are area reduced to that contract).
The flagship Vector and Mongrel retain their512px atlases.
RLE and dropping fully opaque alpha preserve decoded RGBA pixels exactly.
Unused menu padding is cleared outside its verified native crop.
"""
import argparse
from pathlib import Path
import struct
from genportraitsheet import read_tga

ROOT=Path(__file__).resolve().parents[1]
COMPACT={'wp_'+n for n in ['warden','scrapper','lancer','sting','vigil','prowler','bastion','bruiser',
                          'porter','scavenger','scrap','relay','mercc','jakcp','merpp','merwf','jakcs',
                          'outrider','vulture','zenith']}

def encode(rows):
    h=len(rows);w=len(rows[0]);alpha=any(p[3]!=255 for row in rows for p in row)
    step=4 if alpha else 3
    pixels=[bytes((b,g,r,a) if alpha else (b,g,r)) for row in rows for r,g,b,a in row]
    raw=b''.join(pixels);rle=bytearray()
    for y in range(h):
        i=y*w;end=i+w
        while i<end:
            run=1
            while run<128 and i+run<end and pixels[i+run]==pixels[i]:run+=1
            if run>=2:
                rle.append(128+run-1);rle.extend(pixels[i]);i+=run
            else:
                start=i;i+=1
                while i<end and i-start<128:
                    if i+1<end and pixels[i]==pixels[i+1]:break
                    i+=1
                rle.append(i-start-1);rle.extend(b''.join(pixels[start:i]))
    use_rle=len(rle)<len(raw)
    header=bytearray(18);header[2]=10 if use_rle else 2
    struct.pack_into('<HH',header,12,w,h);header[16]=step*8;header[17]=32+(8 if alpha else 0)
    return header+(rle if use_rle else raw)

def reduce_half(rows):
    h=len(rows);w=len(rows[0])
    return [[tuple(round(sum(rows[y+dy][x+dx][c] for dy in (0,1) for dx in (0,1))/4) for c in range(4))
             for x in range(0,w,2)] for y in range(0,h,2)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=ROOT/'data');ap.add_argument('--check',action='store_true')
    args=ap.parse_args();before=after=changed=0
    for path in sorted((args.data/'Art').rglob('*.tga')):
        old=path.read_bytes();rows=read_tga(path)
        if path.stem in COMPACT and len(rows)==512 and len(rows[0])==512:rows=reduce_half(rows)
        # Rock/barrier surfaces have no small markings and occupy only a few
        # dozen screen pixels. Their original source contract is128px.
        if path.stem in ('wp_rock','wp_wall') and len(rows)==256:rows=reduce_half(rows)
        if path.stem=='wp_menu' and len(rows)==512 and len(rows[0])==1024:
            # The native image samples only L57..R967. This padding is never
            # visible, so a solid border saves storage with no on-screen loss.
            mapping=args.data/'Data/INI/MappedImages/HandCreated/WPMenuArt.ini'
            if 'Left:57 Top:0 Right:967 Bottom:512' not in mapping.read_text():
                raise ValueError('Menu crop changed; review padding optimization before writing')
            rows=[[(19,25,29,255)]*57+row[57:967]+[(19,25,29,255)]*57 for row in rows]
        new=encode(rows);before+=len(old);after+=len(new)
        if new!=old:
            changed+=1
            if not args.check:
                temporary=path.with_name('.'+path.name+'.tmp')
                temporary.write_bytes(new)
                if read_tga(temporary)!=rows:raise RuntimeError(f'RLE pixel verification failed: {path}')
                temporary.replace(path)
    print(f'ART_OPTIMIZE {changed} files: {before/1048576:.2f} -> {after/1048576:.2f} MiB; saved {(before-after)/1048576:.2f} MiB')

if __name__=='__main__':main()

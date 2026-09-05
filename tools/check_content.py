#!/usr/bin/env python3
"""Validate asset references and W3D integrity; optionally refresh the asset registry.

Run before staging. This catches content that exists in INI/WND text but would
otherwise become an invisible model, missing portrait or silent sample at runtime.
It does not certify artistic quality or replace an in-game review.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def chunks(data: bytes, start=0, end=None):
    end = len(data) if end is None else end
    offset = start
    while offset < end:
        if offset + 8 > end:
            raise ValueError(f'truncated chunk header at {offset}')
        kind, encoded = struct.unpack_from('<II', data, offset)
        size = encoded & 0x7fffffff
        boundary = offset + 8 + size
        if boundary > end:
            raise ValueError(f'chunk {kind:#x} extends beyond its parent')
        yield kind, data[offset + 8:boundary]
        if encoded & 0x80000000:
            yield from chunks(data, offset + 8, boundary)
        offset = boundary


def w3d_info(path: Path):
    tris = 0
    textures = set()
    for kind, payload in chunks(path.read_bytes()):
        if kind == 0x20:
            if len(payload) % 32:
                raise ValueError('triangle chunk has invalid length')
            tris += len(payload) // 32
        if kind == 0x32:
            name = payload.split(b'\0')[0].decode('ascii', errors='replace')
            if name:
                textures.add(name)
    return tris, sorted(textures)


def audit(write_registry=False):
    failures = []
    models = {p.stem.lower(): p for p in (DATA / 'Art/W3D').glob('*.w3d')}
    textures = {p.name.lower(): p for folder in ('Textures', 'Terrain') for p in (DATA / 'Art' / folder).iterdir() if p.is_file()}
    images = set()
    strings = set(re.findall(r'^([\w]+:[\w]+)\s*$', (DATA / 'Data/Generals.str').read_text(), re.M))
    for path in (DATA / 'Data/INI/MappedImages').rglob('*.ini'):
        text = path.read_text()
        images.update(re.findall(r'^MappedImage\s+(\w+)', text, re.M))
        for texture in re.findall(r'^\s*Texture\s*=\s*(\S+)', text, re.M):
            if texture.lower() not in textures:
                failures.append(f'{path.relative_to(ROOT)}: missing portrait texture {texture}')
    for path in (DATA / 'Data/INI').rglob('*.ini'):
        text = re.sub(r';[^\n]*', '', path.read_text())
        for model in re.findall(r'^\s*Model\s*=\s*([\w.]+)', text, re.M):
            if model.upper() not in ('NONE', 'NULL') and model.lower() not in models:
                failures.append(f'{path.relative_to(ROOT)}: missing model {model}')
        for image in re.findall(r'^\s*(?:ButtonImage|SelectPortrait)\s*=\s*(\w+)', text, re.M):
            if image not in images:
                failures.append(f'{path.relative_to(ROOT)}: missing mapped image {image}')
    for path in (DATA / 'Window').rglob('*.wnd'):
        text = path.read_text()
        names = re.findall(r'^\s*NAME\s*=\s*"([^"]+)"', text, re.M)
        if len(names) != len(set(names)):
            failures.append(f'{path.relative_to(ROOT)}: duplicate window names')
        for key in re.findall(r'\bTEXT\s*=\s*"([^"]+)"', text):
            if re.fullmatch(r'\w+:\w+', key) and key not in strings:
                failures.append(f'{path.relative_to(ROOT)}: missing text {key}')
    contract_file = ROOT / 'tools/blender/polish_assets.json'
    contracts = json.loads(contract_file.read_text()) if contract_file.exists() else {}
    if 'assets' in contracts:
        contracts = contracts['assets']
    registry = []
    for name, path in sorted(models.items()):
        try:
            count, referenced = w3d_info(path)
            for texture in referenced:
                if texture.lower() not in textures:
                    failures.append(f'{path.relative_to(ROOT)}: missing model texture {texture}')
            if count > 12000:
                failures.append(f'{path.relative_to(ROOT)}: {count} triangles exceeds the 12k hard ceiling')
            contract = contracts.get(name, {}) if isinstance(contracts, dict) else next((c for c in contracts if c.get('model', '').lower() == name), {})
            registry.append({
                'id': name, 'path': path.relative_to(ROOT).as_posix(),
                'triangles': count, 'bytes': path.stat().st_size, 'textures': referenced,
                'source': contract.get('source', 'See ASSETS.md and tools/ generators'),
                'productionStatus': 'production-pass' if contract else 'existing-content',
                'turret': bool(contract.get('turret')), 'muzzle': bool(contract.get('muzzle')),
                'license': 'CC BY 4.0; see ASSETS.md for per-file provenance',
            })
        except (ValueError, struct.error) as error:
            failures.append(f'{path.relative_to(ROOT)}: invalid W3D: {error}')
    operations = json.loads((DATA / 'operations.json').read_text())
    ids = {mission['id'] for mission in operations['missions']}
    if len(ids) != len(operations['missions']):
        failures.append('operations.json: duplicate mission IDs')
    for mission in operations['missions']:
        if not (DATA / 'Maps' / mission['map'] / f"{mission['map']}.map").exists():
            failures.append(f"Missing map for mission {mission['id']}")
        if 'unlock' in mission:
            failures.append(f"{mission['id']}: operation access must not depend on a browser record")
        for field in ('nextMission',):
            if mission.get(field) and mission[field] not in ids:
                failures.append(f"{mission['id']}: unknown {field} {mission[field]}")
    for failure in sorted(set(failures)):
        print(f'ERROR: {failure}', file=sys.stderr)
    if failures:
        return 1
    if write_registry:
        (DATA / 'asset-registry.json').write_text(json.dumps({'schemaVersion': 1, 'assets': registry}, indent=2) + '\n')
    print(f'Content references OK: {len(models)} W3D files, {len(textures)} textures, {len(images)} mapped images, {len(ids)} authored missions.')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-registry', action='store_true')
    args = parser.parse_args()
    sys.exit(audit(args.write_registry))

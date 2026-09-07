#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
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
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wp_w3d import TEXTURE_NAME, TRIANGLES, walk  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
CATALOG = ROOT / 'tools/blender/polish_assets.json'
TRIANGLE_CEILING = 12000


def w3d_info(path: Path):
    tris = 0
    textures = set()
    for kind, payload in walk(path.read_bytes()):
        if kind == TRIANGLES:
            if len(payload) % 32:
                raise ValueError('triangle chunk has invalid length')
            tris += len(payload) // 32
        if kind == TEXTURE_NAME:
            name = payload.split(b'\0')[0].decode('ascii', errors='replace')
            if name:
                textures.add(name)
    return tris, sorted(textures)


def strip_comments(text: str) -> str:
    return re.sub(r';[^\n]*', '', text)


def object_blocks(text: str):
    """(name, body) for every top-level ``Object`` template in an INI file."""
    return re.findall(r'(?ms)^Object\s+(\w+)[ \t]*$(.*?)^End[ \t]*$', strip_comments(text))


def projectile_conflicts(objects_ini: str, catalog_models) -> list[str]:
    """A projectile's model must be exclusive: sharing it with a prop or any
    non-projectile object draws that scenery in flight (the WPROCK01 boulder
    once flew as every Lancer and Sting rocket)."""
    projectile_users: dict[str, set[str]] = {}
    other_users: dict[str, set[str]] = {}
    for name, body in object_blocks(objects_ini):
        is_projectile = re.search(r'^\s*KindOf\s*=.*\bPROJECTILE\b', body, re.M) is not None
        for model in re.findall(r'^\s*Model\s*=\s*([\w.]+)', body, re.M):
            if model.upper() in ('NONE', 'NULL'):
                continue
            (projectile_users if is_projectile else other_users).setdefault(model.lower(), set()).add(name)
    catalog = {model.lower() for model in catalog_models}
    failures = []
    for model, projectiles in sorted(projectile_users.items()):
        shared = sorted(other_users.get(model, ()))
        if shared:
            failures.append(f'projectile model {model.upper()} ({", ".join(sorted(projectiles))}) '
                            f'is also drawn by non-projectile object(s) {", ".join(shared)}')
        if model in catalog:
            failures.append(f'projectile model {model.upper()} ({", ".join(sorted(projectiles))}) '
                            f'is a production prop in tools/blender/polish_assets.json')
    return failures


def audit(write_registry=False, data: Path = DATA, catalog_path: Path = CATALOG):
    failures = []

    def rel(path: Path) -> str:
        try:
            return path.relative_to(ROOT).as_posix()
        except ValueError:
            return path.as_posix()

    models = {p.stem.lower(): p for p in (data / 'Art/W3D').glob('*.w3d')}
    textures = {p.name.lower(): p for folder in ('Textures', 'Terrain') for p in (data / 'Art' / folder).iterdir() if p.is_file()}
    images = set()
    strings = set(re.findall(r'^([\w]+:[\w]+)\s*$', (data / 'Data/Generals.str').read_text(), re.M))
    for path in (data / 'Data/INI/MappedImages').rglob('*.ini'):
        text = path.read_text()
        images.update(re.findall(r'^MappedImage\s+(\w+)', text, re.M))
        for texture in re.findall(r'^\s*Texture\s*=\s*(\S+)', text, re.M):
            if texture.lower() not in textures:
                failures.append(f'{rel(path)}: missing portrait texture {texture}')
    for path in (data / 'Data/INI').rglob('*.ini'):
        text = strip_comments(path.read_text())
        for model in re.findall(r'^\s*Model\s*=\s*([\w.]+)', text, re.M):
            if model.upper() not in ('NONE', 'NULL') and model.lower() not in models:
                failures.append(f'{rel(path)}: missing model {model}')
        for image in re.findall(r'^\s*(?:ButtonImage|SelectPortrait)\s*=\s*(\w+)', text, re.M):
            if image not in images:
                failures.append(f'{rel(path)}: missing mapped image {image}')
    for path in (data / 'Window').rglob('*.wnd'):
        text = path.read_text()
        names = re.findall(r'^\s*NAME\s*=\s*"([^"]+)"', text, re.M)
        if len(names) != len(set(names)):
            failures.append(f'{rel(path)}: duplicate window names')
        for key in re.findall(r'\bTEXT\s*=\s*"([^"]+)"', text):
            if re.fullmatch(r'\w+:\w+', key) and key not in strings:
                failures.append(f'{rel(path)}: missing text {key}')
    contracts = json.loads(catalog_path.read_text()) if catalog_path.exists() else {}
    objects_ini = data / 'Data/INI/Default/Object.ini'
    failures += [f'{rel(objects_ini)}: {failure}' for failure in projectile_conflicts(objects_ini.read_text(), contracts)]
    registry = []
    for name, path in sorted(models.items()):
        try:
            count, referenced = w3d_info(path)
            for texture in referenced:
                if texture.lower() not in textures:
                    failures.append(f'{rel(path)}: missing model texture {texture}')
            if count > TRIANGLE_CEILING:
                failures.append(f'{rel(path)}: {count} triangles exceeds the {TRIANGLE_CEILING // 1000}k hard ceiling')
            contract = contracts.get(name, {})
            registry.append({
                'id': name, 'path': rel(path),
                'triangles': count, 'bytes': path.stat().st_size, 'textures': referenced,
                'source': contract.get('source', 'See ASSETS.md and tools/ generators'),
                'productionStatus': 'production-pass' if contract else 'existing-content',
                'turret': bool(contract.get('turret')), 'muzzle': bool(contract.get('muzzle')),
                'license': 'CC BY 4.0; see ASSETS.md for per-file provenance',
            })
        except ValueError as error:
            failures.append(f'{rel(path)}: invalid W3D: {error}')
    operations = json.loads((data / 'operations.json').read_text())
    ids = {mission['id'] for mission in operations['missions']}
    if len(ids) != len(operations['missions']):
        failures.append('operations.json: duplicate mission IDs')
    for mission in operations['missions']:
        if not (data / 'Maps' / mission['map'] / f"{mission['map']}.map").exists():
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
        (data / 'asset-registry.json').write_text(json.dumps({'schemaVersion': 1, 'assets': registry}, indent=2) + '\n')
    print(f'Content references OK: {len(models)} W3D files, {len(textures)} textures, {len(images)} mapped images, {len(ids)} authored missions.')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', type=Path, default=DATA, help='dataset root (default: the repository data/)')
    parser.add_argument('--write-registry', action='store_true',
                        help='rewrite <data>/asset-registry.json when every check passes')
    args = parser.parse_args(argv)
    return audit(args.write_registry, args.data.resolve())


if __name__ == '__main__':
    sys.exit(main())

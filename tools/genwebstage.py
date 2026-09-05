#!/usr/bin/env python3
"""Assemble a reproducible, content-addressed browser release from repo sources.

The manifest maps engine paths to immutable asset URLs. A separate build.json
is the only discovery document; normal visits never use timestamp cache busters.
The stage contains the runnable game and its notices, never source credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DATA_DIRS = ('Data', 'Maps', 'Art', 'Window')
MAX_STAGED_BYTES = 64 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> bytes:
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def stage_release(destination: Path, build_dir: Path, run_checks: bool = True) -> dict:
    destination = destination.resolve()
    build_dir = build_dir.resolve()
    root = ROOT.resolve()
    protected = tuple(root / name for name in ('data', 'engine', 'web', 'dvijoke', 'tools', 'tests', 'docs', 'refs'))
    # Legacy stages and compiler outputs can both contain GeneralsXZH.wasm.
    # Check path ownership before trusting that marker and replacing a tree.
    if (destination == root or destination in root.parents or '.git' in destination.parts
            or (destination / '.git').exists() or (destination / '.git').is_symlink()
            or destination == build_dir or destination in build_dir.parents or build_dir in destination.parents
            or any(destination == source or source in destination.parents for source in protected)):
        raise ValueError('Choose a dedicated generated output directory.')
    if destination.exists() and not any((destination / marker).exists() for marker in ('build.json', 'GeneralsXZH.wasm')):
        if any(destination.iterdir()):
            raise ValueError(f'Refusing to replace an unrecognized output directory: {destination}')
    for name in ('GeneralsXZH.js', 'GeneralsXZH.wasm'):
        if not (build_dir / name).is_file():
            raise FileNotFoundError(f'Missing {build_dir / name}. Build the wasm target first.')
    if run_checks:
        for gate in ('lint_voices.py', 'validate_gameplay.py', 'check_content.py'):
            subprocess.run([sys.executable, str(ROOT / 'tools' / gate)], check=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.warpowers-stage-', dir=destination.parent))
    try:
        (temporary / 'assets').mkdir()
        manifest = []
        fingerprint = hashlib.sha256()

        def asset(source: Path) -> dict:
            content = source.read_bytes()
            sha = digest(content)
            relative = f'assets/{sha[:24]}{source.suffix.lower()}'
            target = temporary / relative
            if not target.exists():
                target.write_bytes(content)
            return {'url': relative, 'size': len(content), 'sha256': sha}

        for directory in DATA_DIRS:
            for source in sorted((ROOT / 'data' / directory).rglob('*')):
                if not source.is_file() or any(part.startswith('.') for part in source.relative_to(ROOT / 'data').parts):
                    continue
                descriptor = asset(source)
                relative = source.relative_to(ROOT / 'data').as_posix()
                manifest.append({'p': relative, 's': descriptor['size'], 'u': descriptor['url'], 'h': descriptor['sha256']})
                fingerprint.update(relative.encode() + b'\0' + descriptor['sha256'].encode())
        engine = {kind: asset(build_dir / f'GeneralsXZH.{kind}') for kind in ('js', 'wasm')}
        fingerprint.update(engine['wasm']['sha256'].encode())
        font = asset(ROOT / 'data/Fonts/LiberationSans-Regular.ttf')
        operation_asset = asset(ROOT / 'data/operations.json')
        manifest_bytes = (json.dumps(manifest, separators=(',', ':')) + '\n').encode()
        manifest_name = f'assets/manifest.{digest(manifest_bytes)[:16]}.json'
        (temporary / manifest_name).write_bytes(manifest_bytes)

        # Bundle the tiny UI without a JavaScript dependency or build framework.
        core = (ROOT / 'web/core.js').read_bytes()
        core_name = f'core.{digest(core)[:16]}.js'
        (temporary / core_name).write_bytes(core)
        app = (ROOT / 'web/app.js').read_text().replace("'./core.js'", f"'./{core_name}'").encode()
        app_name = f'app.{digest(app)[:16]}.js'
        (temporary / app_name).write_bytes(app)
        styles = (ROOT / 'web/styles.css').read_text().replace('fonts/default.ttf', font['url']).encode()
        style_name = f'styles.{digest(styles)[:16]}.css'
        (temporary / style_name).write_bytes(styles)
        page = (ROOT / 'web/index.html').read_text().replace('href="styles.css"', f'href="{style_name}"').replace('src="app.js"', f'src="{app_name}"')
        (temporary / 'index.html').write_text(page)
        compatibility = fingerprint.hexdigest()[:20]
        release_id = digest(fingerprint.digest() + app + styles + page.encode()
                            + engine['js']['sha256'].encode() + operation_asset['sha256'].encode())[:12]
        config = {
            'schemaVersion': 1, 'id': release_id, 'compatibility': compatibility,
            'engine': engine, 'font': font, 'manifest': manifest_name,
            'operations': operation_asset['url'], 'dataFiles': len(manifest),
            'dataBytes': sum(entry['s'] for entry in manifest),
        }
        write_json(temporary / 'build.json', config)
        notices = {
            'CREDITS.md': ROOT / 'CREDITS.md', 'ASSETS.md': ROOT / 'ASSETS.md',
            'LICENSING.md': ROOT / 'LICENSING.md', 'LICENSE.txt': ROOT / 'LICENSE',
            'ENGINE-LICENSE.md': ROOT / 'engine/LICENSE.md',
            'DVIJOKE-LICENSE.txt': ROOT / 'dvijoke/LICENSE',
            'FONT-LICENSE.txt': ROOT / 'data/Fonts/LICENSE-LiberationFonts',
        }
        (temporary / 'licenses').mkdir()
        for name, source in notices.items():
            shutil.copyfile(source, temporary / 'licenses' / name)
        credits = (ROOT / 'web/credits.html').read_text().replace('href="styles.css"', f'href="{style_name}"')
        credits = credits.replace('{{BUILD}}', html.escape(release_id))
        (temporary / 'credits.html').write_text(credits)
        staged_bytes = sum(p.stat().st_size for p in temporary.rglob('*') if p.is_file())
        if staged_bytes > MAX_STAGED_BYTES:
            raise ValueError(f'Staged bundle is {staged_bytes:,} bytes; the limit is '
                             f'{MAX_STAGED_BYTES:,}. Reduce content before publishing.')
        # This directory is generated output, validated above; sources remain untouched.
        if destination.exists():
            shutil.rmtree(destination)
        temporary.replace(destination)
        config['stagedBytes'] = staged_bytes
        return config
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?', type=Path, default=ROOT / 'webstage')
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'engine/build/wasm/GeneralsMD')
    parser.add_argument('--skip-checks', action='store_true', help='Only for isolated packaging tests; never use for a release.')
    args = parser.parse_args()
    result = stage_release(args.destination, args.build_dir, not args.skip_checks)
    print(f"Staged {result['dataFiles']} data files, {result['stagedBytes'] / 1048576:.1f} MiB; build {result['id']} -> {args.destination}")


if __name__ == '__main__':
    main()

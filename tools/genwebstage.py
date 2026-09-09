#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Assemble a reproducible, content-addressed browser release from repo sources.

The manifest maps engine paths to immutable asset URLs. A separate build.json
is the only discovery document; normal visits never use timestamp cache busters.
The stage contains the runnable game and its notices, never source credentials.

Files in web/static/ (icons, the social card, site.webmanifest, robots.txt and
404.html) are copied to the stage root under their own names, because browsers
and link previews fetch them by fixed address. --public-url (default
https://warpowers.vercel.app; an https origin with an optional path, no
trailing slash) fills the {{PUBLIC_URL}} token in index.html, credits.html and
404.html, whose canonical links and preview images need absolute URLs. Static
files and the public URL change the release id, never the save compatibility
hash.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import string
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA_DIRS = ('Data', 'Maps', 'Art', 'Window')
MAX_STAGED_BYTES = 64 * 1024 * 1024
DEFAULT_PUBLIC_URL = 'https://warpowers.vercel.app'
PUBLIC_URL_TOKEN = '{{PUBLIC_URL}}'
# The public URL lands verbatim inside HTML attributes, so only plain URL characters are accepted.
PUBLIC_URL_CHARACTERS = frozenset(string.ascii_letters + string.digits + '-._~:/%')
STATIC_DIR = 'web/static'
STATIC_FILES = ('favicon.svg', 'favicon.ico', 'favicon-32.png', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png',
                'social-card.jpg', 'site.webmanifest', 'robots.txt', '404.html')
# Generated release files and the content-addressed bundle prefixes; a static file of the same name would shadow them.
RESERVED_STAGE_NAMES = frozenset({'index.html', 'credits.html', 'build.json', 'source.json', 'assets', 'licenses'})
HASHED_PREFIXES = ('app.', 'core.', 'styles.')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> bytes:
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def read_notices(root: Path) -> dict[str, bytes]:
    """Read only declared notices; missing license material aborts staging."""
    files = {
        'CREDITS.md': root / 'CREDITS.md', 'ASSETS.md': root / 'ASSETS.md',
        # Preserve the browser download URL when the repository guide is renamed.
        'LICENSING.md': root / 'LICENSING.md', 'LICENSE.txt': root / 'LICENSE',
        'ENGINE-LICENSE.md': root / 'engine/LICENSE.md',
        'DVIJOKE-LICENSE.txt': root / 'dvijoke/LICENSE',
        'FONT-LICENSE.txt': root / 'data/Fonts/LICENSE-LiberationFonts',
        'third-party.json': root / 'licenses/third-party.json',
    }
    manifest = json.loads(files['third-party.json'].read_text())
    components = manifest.get('components')
    if manifest.get('schemaVersion') != 1 or not isinstance(components, list) or not components:
        raise ValueError('The third-party license inventory must contain components (schemaVersion 1).')
    ids = set()
    license_root = (root / 'licenses').resolve()
    for component in components:
        if not isinstance(component, dict) or any(
                not isinstance(component.get(key), str) or not component[key].strip()
                for key in ('id', 'name', 'version', 'license', 'source', 'notice')):
            raise ValueError('Each license component needs an id, name, version, license, source and notice.')
        if component['id'] in ids:
            raise ValueError(f"Duplicate license component: {component['id']}")
        ids.add(component['id'])
        relative = Path(component['notice'])
        source = license_root / relative
        if (relative.is_absolute() or '..' in relative.parts or len(relative.parts) < 2
                or relative.parts[0] != 'third-party'
                or license_root not in source.resolve().parents):
            raise ValueError(f"License notice must stay inside licenses/third-party/: {relative}")
        files[relative.as_posix()] = source
    notices = {name: path.read_bytes() for name, path in files.items()}
    for name, content in notices.items():
        if not content.strip():
            raise ValueError(f'Empty required license notice: {name}')
    return notices


def read_static_files(root: Path) -> dict[str, bytes]:
    """Read web/static/: every regular file ships unhashed at the stage root, and the expected set must be complete."""
    directory = root / STATIC_DIR
    restore = 'Restore web/static/ from the repository; the icons come from python3 tools/genstatic.py.'
    if not directory.is_dir():
        raise FileNotFoundError(f'Missing {directory}. {restore}')
    files = {}
    for source in sorted(directory.iterdir()):
        if source.name.startswith('.'):
            continue  # editor and Finder metadata never ship
        if not source.is_file():
            raise ValueError(f'{STATIC_DIR}/{source.name} is not a regular file; only files are staged.')
        if source.name in RESERVED_STAGE_NAMES or source.name.startswith(HASHED_PREFIXES):
            raise ValueError(f'{STATIC_DIR}/{source.name} would shadow a generated release file.')
        files[source.name] = source.read_bytes()
    for name in STATIC_FILES:
        if name not in files:
            raise FileNotFoundError(f'Missing {directory / name}. {restore}')
        if not files[name].strip():
            raise ValueError(f'Empty static file: {STATIC_DIR}/{name}')
    return files


def split_https_url(url: str, error: str):
    """Shared checks for URLs that end up in the stage: https, a host, a valid port, no credentials or whitespace."""
    try:
        parts = urlsplit(url)
        # urlsplit defers malformed and out-of-range port errors until access.
        _ = parts.port
    except ValueError as cause:
        raise ValueError(error) from cause
    if (parts.scheme != 'https' or not parts.hostname or parts.username is not None or parts.password is not None
            or any(character.isspace() or ord(character) < 32 for character in url)):
        raise ValueError(error)
    return parts


def validate_source_url(source_url: str | None, release: bool) -> None:
    if not source_url:
        if release:
            raise ValueError('Public release staging requires --source-url pointing to complete corresponding source.')
        return
    split_https_url(source_url, 'The source URL must be an HTTPS URL without credentials or whitespace and with a valid port.')


def validate_public_url(public_url: str) -> None:
    """An https origin with an optional path prefix; the token substitution appends '/' and file names to it."""
    error = ('The public URL must be an https:// origin with an optional path and no trailing slash, credentials, '
             f'query, fragment or unusual characters, for example {DEFAULT_PUBLIC_URL}')
    if (not isinstance(public_url, str) or not public_url or public_url.endswith('/')
            or set(public_url) - PUBLIC_URL_CHARACTERS):
        raise ValueError(error)
    split_https_url(public_url, error)


def stage_release(destination: Path, build_dir: Path, run_checks: bool = True,
                  *, source_url: str | None = None, release: bool = False,
                  public_url: str = DEFAULT_PUBLIC_URL) -> dict:
    validate_source_url(source_url, release)
    validate_public_url(public_url)
    if release and not run_checks:
        raise ValueError('Public release staging cannot skip content checks.')
    destination = destination.resolve()
    build_dir = build_dir.resolve()
    root = ROOT.resolve()
    protected = tuple(root / name for name in ('data', 'engine', 'web', 'dvijoke', 'tools', 'tests', 'docs', 'refs', 'licenses'))
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
    notices = read_notices(root)
    static_files = read_static_files(root)
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
        page = page.replace(PUBLIC_URL_TOKEN, public_url)
        (temporary / 'index.html').write_text(page)
        source_message = (f'<a href="{html.escape(source_url, quote=True)}">Corresponding source for this build</a>.'
                          if source_url else 'Unreleased development build. Corresponding source will be available with the public release.')
        credits = (ROOT / 'web/credits.html').read_text().replace('href="styles.css"', f'href="{style_name}"')
        credits = credits.replace('{{SOURCE}}', source_message).replace(PUBLIC_URL_TOKEN, public_url)
        components = json.loads(notices['third-party.json'])['components']
        dependency_links = ''.join(
            f'<li><a href="licenses/{html.escape(component["notice"], quote=True)}">'
            f'{html.escape(component["name"])} {html.escape(component["version"])}</a>'
            f' · {html.escape(component["license"])}</li>' for component in components)
        credits = credits.replace('{{DEPENDENCY_NOTICES}}', dependency_links)
        # Fixed-name files: browsers and link previews fetch these by address, so they are never hashed.
        # Only HTML pages carry the public URL token (404.html is served for any missing path).
        static_hash = hashlib.sha256()
        for name, content in sorted(static_files.items()):
            if name.endswith('.html'):
                content = content.decode().replace(PUBLIC_URL_TOKEN, public_url).encode()
            elif PUBLIC_URL_TOKEN.encode() in content:
                raise ValueError(f'{STATIC_DIR}/{name}: {PUBLIC_URL_TOKEN} is only substituted in HTML files.')
            (temporary / name).write_bytes(content)
            static_hash.update(name.encode() + b'\0' + digest(content).encode())
        notice_hash = hashlib.sha256()
        for name, content in sorted(notices.items()):
            notice_hash.update(name.encode() + b'\0' + digest(content).encode())
        compatibility = fingerprint.hexdigest()[:20]
        release_id = digest(fingerprint.digest() + app + styles + page.encode()
                            + engine['js']['sha256'].encode() + operation_asset['sha256'].encode()
                            + notice_hash.digest() + credits.encode() + (source_url or '').encode()
                            + static_hash.digest())[:12]
        config = {
            'schemaVersion': 1, 'id': release_id, 'compatibility': compatibility,
            'engine': engine, 'font': font, 'manifest': manifest_name,
            'operations': operation_asset['url'], 'dataFiles': len(manifest),
            'dataBytes': sum(entry['s'] for entry in manifest),
            'source': 'source.json',
        }
        write_json(temporary / 'build.json', config)
        # The URL is supplied by the releaser, not proof that source reproduces
        # these bytes. Signed-out access and rebuilding remain release checks.
        write_json(temporary / 'source.json', {
            'schemaVersion': 1, 'build': release_id,
            'status': 'provided' if source_url else 'development', 'url': source_url,
            'engine': {kind: {'sha256': item['sha256'], 'size': item['size']} for kind, item in engine.items()},
            'dependencies': 'licenses/third-party.json',
        })
        for name, content in notices.items():
            target = temporary / 'licenses' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
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


def public_url_argument(value: str) -> str:
    try:
        validate_public_url(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('destination', nargs='?', type=Path, default=ROOT / 'webstage')
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'engine/build/wasm/GeneralsMD')
    parser.add_argument('--skip-checks', action='store_true', help='Only for isolated packaging tests; never use for a release.')
    parser.add_argument('--source-url', help='HTTPS link to complete corresponding source for this build (archive or release source page).')
    parser.add_argument('--public-url', type=public_url_argument, default=DEFAULT_PUBLIC_URL,
                        help='https address the release is served from, without a trailing slash; fills the canonical '
                             'links, preview images and 404 page (default: %(default)s).')
    parser.add_argument('--release', action='store_true', help='Require a source link and content checks for a public release candidate; never deploys.')
    args = parser.parse_args()
    result = stage_release(args.destination, args.build_dir, not args.skip_checks,
                           source_url=args.source_url, release=args.release, public_url=args.public_url)
    print(f"Staged {result['dataFiles']} data files, {result['stagedBytes'] / 1048576:.1f} MiB; build {result['id']} -> {args.destination}")


if __name__ == '__main__':
    main()

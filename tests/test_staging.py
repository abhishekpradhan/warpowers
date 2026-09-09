# SPDX-License-Identifier: MIT
"""Release packaging invariants, exercised against a tiny isolated source tree, plus the static icon generator."""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

REPO = Path(__file__).parents[1]


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, REPO / 'tools' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


staging = load_tool('genwebstage')
genstatic = load_tool('genstatic')

STATIC_FIXTURE = {
    'favicon.svg': b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"/>',
    'favicon.ico': b'\x00\x00\x01\x00 ico', 'favicon-32.png': b'\x89PNG 32', 'apple-touch-icon.png': b'\x89PNG 180',
    'icon-192.png': b'\x89PNG 192', 'icon-512.png': b'\x89PNG 512', 'social-card.jpg': b'\xff\xd8 card',
    'site.webmanifest': b'{"name":"War Powers","start_url":"/"}', 'robots.txt': b'User-agent: *\nAllow: /\n',
    '404.html': b'<link rel="icon" href="{{PUBLIC_URL}}/favicon.svg"><a href="/">Nothing is stationed here.</a>',
}


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='warpowers-stage-test-')
        self.root = Path(self.temp.name)
        self.original_root = staging.ROOT
        staging.ROOT = self.root
        for name, value in {
            'data/Data/rules.ini': b'original rules', 'data/operations.json': b'{"missions":[]}',
            'data/Fonts/LiberationSans-Regular.ttf': b'font', 'data/Fonts/LICENSE-LiberationFonts': b'font notice',
            'engine/build/wasm/GeneralsMD/GeneralsXZH.js': b'var Module = {};',
            'engine/build/wasm/GeneralsMD/GeneralsXZH.wasm': b'engine fixture',
            'engine/LICENSE.md': b'engine notice', 'dvijoke/LICENSE': b'renderer notice',
            'web/core.js': b'export const a = 1;', 'web/app.js': b"import './core.js';",
            'web/styles.css': b"url('fonts/default.ttf')",
            'web/index.html': b'<link rel="canonical" href="{{PUBLIC_URL}}/"><meta property="og:image" content="{{PUBLIC_URL}}/social-card.jpg">'
                              b'<link href="styles.css"><script src="app.js"></script>',
            'web/credits.html': b'<link rel="canonical" href="{{PUBLIC_URL}}/credits.html">{{BUILD}} {{SOURCE}} <ul>{{DEPENDENCY_NOTICES}}</ul>',
            **{f'web/static/{name}': content for name, content in STATIC_FIXTURE.items()},
            'web/static/.DS_Store': b'finder metadata never ships',
            'CREDITS.md': b'credits', 'ASSETS.md': b'provenance',
            'LICENSING.md': b'license map', 'LICENSE': b'code notice',
            'licenses/third-party.json': json.dumps({'schemaVersion': 1, 'components': [{
                'id': 'fixture', 'name': 'Fixture Library', 'version': '1.0', 'license': 'MIT',
                'source': 'https://example.com/library/1.0', 'notice': 'third-party/fixture.txt',
            }]}).encode(),
            'licenses/third-party/fixture.txt': b'Fixture Library copyright and permission',
        }.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
        self.build_dir = self.root / 'engine/build/wasm/GeneralsMD'
        self.out = self.root / 'out'

    def tearDown(self):
        staging.ROOT = self.original_root
        self.temp.cleanup()

    def stage(self, **kwargs):
        return staging.stage_release(self.out, self.build_dir, False, **kwargs)

    def test_identical_input_has_identical_release_and_save_compatibility(self):
        first = self.stage()
        second = self.stage()
        self.assertEqual(first['id'], second['id'])
        self.assertEqual(first['compatibility'], second['compatibility'])
        self.assertNotIn('Date.now', (self.out / 'index.html').read_text())

    def test_each_logical_asset_has_matching_content_address_and_size(self):
        config = self.stage()
        manifest = json.loads((self.out / config['manifest']).read_text())
        for entry in manifest:
            data = (self.out / entry['u']).read_bytes()
            self.assertEqual(len(data), entry['s'])
            self.assertEqual(staging.digest(data), entry['h'])
        self.assertTrue((self.out / 'licenses/ENGINE-LICENSE.md').exists())
        self.assertTrue((self.out / 'licenses/FONT-LICENSE.txt').exists())
        self.assertEqual((self.out / 'licenses/third-party/fixture.txt').read_bytes(),
                         (self.root / 'licenses/third-party/fixture.txt').read_bytes())
        self.assertIn('href="licenses/third-party/fixture.txt"', (self.out / 'credits.html').read_text())
        self.assertFalse((self.out / '.git').exists())

    def test_missing_or_empty_notice_preserves_previous_stage(self):
        first = self.stage()
        notice = self.root / 'licenses/third-party/fixture.txt'
        notice.unlink()
        with self.assertRaises(FileNotFoundError):
            self.stage()
        self.assertEqual(json.loads((self.out / 'build.json').read_text())['id'], first['id'])
        notice.write_text('  \n')
        with self.assertRaisesRegex(ValueError, 'Empty required license notice'):
            self.stage()
        self.assertEqual(json.loads((self.out / 'build.json').read_text())['id'], first['id'])

    def test_notice_paths_cannot_escape_license_directory(self):
        path = self.root / 'licenses/third-party.json'
        manifest = json.loads(path.read_text())
        outside = self.root / 'private.txt'
        outside.write_text('not a license')
        (self.root / 'licenses/third-party/escape.txt').symlink_to(outside)
        for name in ('../private.txt', str(outside), 'third-party/escape.txt'):
            with self.subTest(notice=name):
                manifest['components'][0]['notice'] = name
                path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, 'must stay inside'):
                    self.stage()

    def test_notice_and_credits_changes_identify_release_without_invalidating_saves(self):
        first = self.stage()
        (self.root / 'licenses/third-party/fixture.txt').write_text('Corrected copyright and permission')
        updated = self.stage()
        self.assertNotEqual(first['id'], updated['id'])
        self.assertEqual(first['compatibility'], updated['compatibility'])
        with (self.root / 'web/credits.html').open('a') as page:
            page.write(' Additional acknowledgment.')
        credits = self.stage()
        self.assertNotEqual(updated['id'], credits['id'])
        self.assertEqual(updated['compatibility'], credits['compatibility'])

    def test_development_and_supplied_source_records_match_distributed_engine(self):
        development = self.stage()
        self.assertEqual(json.loads((self.out / 'source.json').read_text())['status'], 'development')
        url = 'https://example.com/releases/1.0/source?format=tar&download=1'
        provided = self.stage(source_url=url)
        source = json.loads((self.out / provided['source']).read_text())
        self.assertEqual(source['status'], 'provided')
        self.assertEqual(source['url'], url)
        self.assertEqual(source['build'], provided['id'])
        self.assertEqual(source['engine']['wasm']['sha256'], provided['engine']['wasm']['sha256'])
        self.assertEqual(source['dependencies'], 'licenses/third-party.json')
        self.assertIn('format=tar&amp;download=1', (self.out / 'credits.html').read_text())
        self.assertNotEqual(development['id'], provided['id'])
        self.assertEqual(development['compatibility'], provided['compatibility'])

    def test_public_release_requires_source_and_content_checks(self):
        with self.assertRaisesRegex(ValueError, 'requires --source-url'):
            staging.stage_release(self.out, self.build_dir, release=True)
        with self.assertRaisesRegex(ValueError, 'cannot skip'):
            self.stage(source_url='https://example.com/source', release=True)
        with patch.object(staging.subprocess, 'run') as run:
            config = staging.stage_release(self.out, self.build_dir, release=True,
                                           source_url='https://example.com/releases/1.0/source')
        self.assertEqual(run.call_count, 3)
        self.assertEqual(json.loads((self.out / 'source.json').read_text())['build'], config['id'])

    def test_source_urls_reject_credentials_and_unsafe_schemes(self):
        for url in ('javascript:alert(1)', 'http://example.com/source', 'https:///source',
                    'https://user:secret@example.com/source', 'https://example.com/\nsource',
                    'https://example.com:bad/source.tar.gz', 'https://example.com:99999/source.tar.gz',
                    'https://[invalid]/source'):
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, 'HTTPS URL'):
                    self.stage(source_url=url)

    def test_content_changes_invalidate_saves_but_ui_changes_do_not(self):
        first = self.stage()
        (self.root / 'web/app.js').write_text("import './core.js'; console.log('new UI');")
        ui = self.stage()
        self.assertNotEqual(first['id'], ui['id'])
        self.assertEqual(first['compatibility'], ui['compatibility'])
        (self.root / 'data/Data/rules.ini').write_text('new gameplay')
        game = self.stage()
        self.assertNotEqual(ui['compatibility'], game['compatibility'])

    def test_staging_never_replaces_sources_or_unrecognized_directories(self):
        with self.assertRaises(ValueError):
            staging.stage_release(self.root / 'data', self.build_dir, False)
        self.out.mkdir()
        (self.out / 'keep.txt').write_text('user content')
        with self.assertRaises(ValueError):
            self.stage()
        self.assertEqual((self.out / 'keep.txt').read_text(), 'user content')

    def test_build_directory_and_ancestors_survive_legacy_marker(self):
        # Exercise a custom compiler output outside the protected engine tree.
        build_dir = self.root / 'custom-build' / 'compiler'
        build_dir.mkdir(parents=True)
        for name in ('GeneralsXZH.js', 'GeneralsXZH.wasm'):
            (build_dir / name).write_bytes((self.build_dir / name).read_bytes())
        (build_dir.parent / 'build.json').write_text('{}')
        for destination in (self.build_dir, build_dir, build_dir.parent):
            with self.subTest(destination=destination):
                before = {p.relative_to(destination): p.read_bytes()
                          for p in destination.rglob('*') if p.is_file()}
                with self.assertRaises(ValueError):
                    staging.stage_release(destination, build_dir, False)
                self.assertEqual(before, {p.relative_to(destination): p.read_bytes()
                                          for p in destination.rglob('*') if p.is_file()})

    def test_source_subdirectories_and_repository_roots_survive_stage_markers(self):
        for destination in (self.root / 'data' / 'Art', self.root / 'web',
                            self.root / 'tools' / 'generated', self.root / 'licenses',
                            self.root / 'another-repo'):
            with self.subTest(destination=destination):
                destination.mkdir(parents=True, exist_ok=True)
                (destination / 'build.json').write_text('{}')
                (destination / 'keep.txt').write_text('source content')
                if destination.name == 'another-repo':
                    # Git worktrees/submodules use a .git file, not a directory.
                    (destination / '.git').write_text('gitdir: elsewhere')
                with self.assertRaises(ValueError):
                    staging.stage_release(destination, self.build_dir, False)
                self.assertEqual((destination / 'keep.txt').read_text(), 'source content')
                self.assertEqual((destination / 'build.json').read_text(), '{}')

    def test_safe_custom_legacy_stage_can_be_replaced(self):
        self.out.mkdir()
        (self.out / 'GeneralsXZH.wasm').write_bytes(b'old staged engine')
        (self.out / 'old.txt').write_text('old stage')
        config = self.stage()
        self.assertEqual(json.loads((self.out / 'build.json').read_text())['id'], config['id'])
        self.assertFalse((self.out / 'old.txt').exists())

    def test_engine_glue_changes_identify_a_new_release(self):
        first = self.stage()
        (self.build_dir / 'GeneralsXZH.js').write_text('var Module = { updatedGlue: true };')
        second = self.stage()
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(first['compatibility'], second['compatibility'])

    def test_over_budget_release_preserves_previous_working_stage(self):
        first = self.stage()
        original_page = (self.out / 'index.html').read_bytes()
        (self.root / 'web/app.js').write_text("console.log('oversized candidate');")
        with patch.object(staging, 'MAX_STAGED_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'the limit'):
                self.stage()
        self.assertEqual(json.loads((self.out / 'build.json').read_text())['id'], first['id'])
        self.assertEqual((self.out / 'index.html').read_bytes(), original_page)
        self.assertEqual(list(self.root.glob('.warpowers-stage-*')), [])

    def test_static_files_are_staged_unchanged_at_the_root(self):
        self.stage()
        for name, content in STATIC_FIXTURE.items():
            with self.subTest(name=name):
                staged = (self.out / name).read_bytes()
                if name.endswith('.html'):
                    self.assertNotIn(b'{{PUBLIC_URL}}', staged)
                    self.assertIn(b'href="https://warpowers.vercel.app/favicon.svg"', staged)
                else:
                    self.assertEqual(staged, content)
        self.assertEqual(set(STATIC_FIXTURE), set(staging.STATIC_FILES))
        self.assertFalse((self.out / '.DS_Store').exists(), 'dotfiles never ship')
        self.assertFalse(list(self.out.glob('assets/favicon*')), 'static files are never content-addressed')

    def test_public_url_fills_every_page_and_leaves_no_token(self):
        default = self.stage()
        self.assertIn('href="https://warpowers.vercel.app/"', (self.out / 'index.html').read_text())
        self.assertIn('content="https://warpowers.vercel.app/social-card.jpg"', (self.out / 'index.html').read_text())
        self.assertIn('href="https://warpowers.vercel.app/credits.html"', (self.out / 'credits.html').read_text())
        custom = self.stage(public_url='https://play.example.org/war-powers')
        self.assertIn('href="https://play.example.org/war-powers/"', (self.out / 'index.html').read_text())
        self.assertIn('href="https://play.example.org/war-powers/credits.html"', (self.out / 'credits.html').read_text())
        self.assertIn('href="https://play.example.org/war-powers/favicon.svg"', (self.out / '404.html').read_text())
        for path in self.out.rglob('*'):
            if path.is_file() and path.suffix not in ('.png', '.jpg', '.wasm', '.ttf'):
                self.assertNotIn('{{PUBLIC_URL}}', path.read_text(), path.name)
        # A different public address is a different release of the same game.
        self.assertNotEqual(default['id'], custom['id'])
        self.assertEqual(default['compatibility'], custom['compatibility'])

    def test_invalid_public_urls_are_rejected_by_the_api_and_the_flag(self):
        for url in ('https://warpowers.vercel.app/', 'http://warpowers.vercel.app', 'https://user:secret@example.com',
                    'https://example.com/?utm=1', 'https://example.com/#top', 'https://exam ple.com', 'https:///',
                    'https://example.com:99999', 'https://example.com/"><script>', 'javascript:alert(1)', '', None):
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, 'public URL'):
                    self.stage(public_url=url)
                self.assertFalse(self.out.exists())
        argv = ['genwebstage.py', str(self.out), '--skip-checks', '--public-url', 'https://warpowers.vercel.app/']
        with patch.object(staging.sys, 'argv', argv), patch.object(staging.sys, 'stderr', io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as failure:
                staging.main()
        self.assertEqual(failure.exception.code, 2)
        self.assertIn('trailing slash', stderr.getvalue())
        self.assertFalse(self.out.exists())
        argv[-1] = 'https://play.example.org'
        with patch.object(staging.sys, 'argv', argv), patch.object(staging.sys, 'stdout', io.StringIO()) as stdout:
            staging.main()
        self.assertIn('href="https://play.example.org/"', (self.out / 'index.html').read_text())
        self.assertIn(json.loads((self.out / 'build.json').read_text())['id'], stdout.getvalue())

    def test_missing_static_files_abort_without_replacing_previous_stage(self):
        first = self.stage()
        (self.root / 'web/static/social-card.jpg').unlink()
        with self.assertRaisesRegex(FileNotFoundError, 'social-card.jpg'):
            self.stage()
        self.assertEqual(json.loads((self.out / 'build.json').read_text())['id'], first['id'])
        self.assertEqual((self.out / 'social-card.jpg').read_bytes(), STATIC_FIXTURE['social-card.jpg'])
        shutil.rmtree(self.root / 'web/static')
        with self.assertRaisesRegex(FileNotFoundError, 'web/static'):
            self.stage()
        self.assertEqual(json.loads((self.out / 'build.json').read_text())['id'], first['id'])
        self.assertEqual(list(self.root.glob('.warpowers-stage-*')), [])

    def test_static_changes_identify_release_without_invalidating_saves(self):
        first = self.stage()
        (self.root / 'web/static/social-card.jpg').write_bytes(b'\xff\xd8 a better card')
        second = self.stage()
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(first['compatibility'], second['compatibility'])
        self.assertEqual((self.out / 'social-card.jpg').read_bytes(), b'\xff\xd8 a better card')

    def test_static_entries_cannot_shadow_generated_files_or_hide_the_token(self):
        first = self.stage()
        static = self.root / 'web/static'
        for name, content, message in (('index.html', b'<p>shadow</p>', 'shadow'), ('build.json', b'{}', 'shadow'),
                                       ('app.stale.js', b'//', 'shadow'), ('assets', b'', 'shadow'),
                                       ('notes', None, 'not a regular file'),
                                       ('robots.txt', b'Sitemap: {{PUBLIC_URL}}/sitemap.xml\n', 'only substituted in HTML')):
            with self.subTest(name=name):
                target = static / name
                if content is None:
                    target.mkdir()
                else:
                    target.write_bytes(content)
                with self.assertRaisesRegex(ValueError, message):
                    self.stage()
                self.assertEqual(json.loads((self.out / 'build.json').read_text())['id'], first['id'])
                if content is None:
                    target.rmdir()
                elif name in STATIC_FIXTURE:
                    target.write_bytes(STATIC_FIXTURE[name])
                else:
                    target.unlink()
        self.assertEqual(self.stage()['id'], first['id'])


def decode_png(data):
    """Read the generator's own PNG flavour (8-bit RGB, filter 0): (width, height, rows of RGB bytes)."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG')
    width, height = struct.unpack('>II', data[16:24])
    offset, idat = 8, b''
    while offset < len(data):
        length, tag = struct.unpack('>I4s', data[offset:offset + 8])
        if tag == b'IDAT':
            idat += data[offset + 8:offset + 8 + length]
        offset += 12 + length
    raw = zlib.decompress(idat)
    stride = width * 3 + 1
    if len(raw) != stride * height or any(raw[row * stride] != 0 for row in range(height)):
        raise ValueError('unexpected scanline layout')
    return width, height, [raw[row * stride + 1:(row + 1) * stride] for row in range(height)]


class StaticIconTests(unittest.TestCase):
    SVG = REPO / 'web/static/favicon.svg'
    DARK, GOLD = bytes((0x0d, 0x12, 0x18)), bytes((0xd7, 0xb4, 0x5a))

    def pixel(self, rows, x, y):
        return rows[y][3 * x:3 * x + 3]

    def test_favicon_path_parses_to_the_w_polygon(self):
        polygon = genstatic.parse_path('m9 14 8 36h10l5-19 5 19h10l8-36H44l-3 22-4-16H27l-4 16-3-22z')
        self.assertEqual(polygon, [[(9, 14), (17, 50), (27, 50), (32, 31), (37, 50), (47, 50), (55, 14),
                                    (44, 14), (41, 36), (37, 20), (27, 20), (23, 36), (20, 14)]])
        self.assertEqual(genstatic.parse_path('M0 0h64v64H0z'), [[(0, 0), (64, 0), (64, 64), (0, 64)]])
        self.assertEqual(genstatic.parse_path('M1 1 2 1 2 2Z M4,4 5,4 5,5z'), [[(1, 1), (2, 1), (2, 2)], [(4, 4), (5, 4), (5, 5)]])
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            genstatic.parse_path('M0 0c1 1 2 2 3 3z')

    def test_icons_render_the_gold_glyph_on_the_dark_square_reproducibly(self):
        sizes = {'master.png': 64, 'small.png': 16}
        icons = genstatic.generate(self.SVG, master=64, icons=sizes)
        self.assertEqual(icons, genstatic.generate(self.SVG, master=64, icons=sizes), 'a rerun is byte-identical')
        width, height, rows = decode_png(icons['master.png'])
        self.assertEqual((width, height), (64, 64))
        self.assertEqual(self.pixel(rows, 0, 0), self.DARK)
        self.assertEqual(self.pixel(rows, 63, 63), self.DARK)
        self.assertEqual(self.pixel(rows, 15, 22), self.GOLD, 'inside the left stroke')
        self.assertEqual(self.pixel(rows, 32, 25), self.GOLD, 'inside the middle peak, where the two V strokes join')
        self.assertEqual(self.pixel(rows, 32, 16), self.DARK, 'above the middle peak')
        self.assertEqual(self.pixel(rows, 32, 40), self.DARK, 'in the gap below the middle peak')
        self.assertEqual(self.pixel(rows, 32, 58), self.DARK, 'below the glyph')
        pixels = [self.pixel(rows, x, 32) for x in range(64)]
        self.assertTrue(any(p not in (self.DARK, self.GOLD) for p in pixels), 'slanted edges are antialiased')
        self.assertTrue(all(lo <= v <= hi for p in pixels for v, lo, hi in zip(p, self.DARK, self.GOLD)),
                        'every pixel is a blend of the two palette colours')
        width, height, small = decode_png(icons['small.png'])
        self.assertEqual((width, height), (16, 16))
        self.assertEqual(self.pixel(small, 0, 0), self.DARK)
        self.assertEqual(self.pixel(small, 3, 5), self.GOLD, 'the box filter keeps solid areas solid')

    def test_shipped_icons_match_a_fresh_render(self):
        # Pixel comparison, not bytes: the deflate stream may differ between zlib builds.
        for name, data in genstatic.generate(self.SVG).items():
            with self.subTest(icon=name):
                self.assertEqual(decode_png((REPO / 'web/static' / name).read_bytes()), decode_png(data))


if __name__ == '__main__':
    unittest.main()

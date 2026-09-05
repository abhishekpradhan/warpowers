"""Release packaging invariants, exercised against a tiny isolated source tree."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('staging', Path(__file__).parents[1] / 'tools/genwebstage.py')
staging = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(staging)


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
            'web/styles.css': b"url('fonts/default.ttf')", 'web/index.html': b'<link href="styles.css"><script src="app.js"></script>',
            'web/credits.html': b'{{BUILD}}', 'CREDITS.md': b'credits', 'ASSETS.md': b'provenance',
            'LICENSING.md': b'license map', 'LICENSE': b'code notice',
        }.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
        self.build_dir = self.root / 'engine/build/wasm/GeneralsMD'
        self.out = self.root / 'out'

    def tearDown(self):
        staging.ROOT = self.original_root
        self.temp.cleanup()

    def stage(self):
        return staging.stage_release(self.out, self.build_dir, False)

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
        self.assertFalse((self.out / '.git').exists())

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


if __name__ == '__main__':
    unittest.main()

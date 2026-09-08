# SPDX-License-Identifier: MIT
"""Unit tests for the content tooling under tools/ (standard library only, no Blender)."""
import contextlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import check_content  # noqa: E402
import genmap  # noqa: E402
import gentex  # noqa: E402
import genw3d  # noqa: E402
import validate_gameplay  # noqa: E402
import w3dhierarchy  # noqa: E402
import wp_tga  # noqa: E402
import wp_w3d  # noqa: E402


class TgaTests(unittest.TestCase):
    def test_header_fields(self):
        header = wp_tga.header(300, 7, alpha=True, rle=True, top_left=True)
        self.assertEqual(len(header), wp_tga.HEADER_SIZE)
        self.assertEqual(header[2], wp_tga.RLE)
        self.assertEqual(struct.unpack_from('<HH', header, 12), (300, 7))
        self.assertEqual(header[16], 32)
        self.assertEqual(header[17], wp_tga.TOP_LEFT | 8)
        plain = wp_tga.header(2, 2)
        self.assertEqual((plain[2], plain[16], plain[17]), (wp_tga.UNCOMPRESSED, 24, wp_tga.TOP_LEFT))

    def test_rle_round_trip_keeps_pixels_and_drops_unused_alpha(self):
        rows = [[(10, 20, 30, 255)] * 40 + [(200, 100, 0, 255)] * 24 for _ in range(3)]
        data = wp_tga.encode(rows)
        self.assertEqual(data[2], wp_tga.RLE)
        self.assertEqual(data[16], 24, 'fully opaque alpha must not be stored')
        self.assertEqual(wp_tga.decode(data), rows)

    def test_literal_runs_and_translucent_alpha_round_trip(self):
        rows = [[((x * 37) % 256, (y * 91) % 256, (x * y) % 256, 128 + (x % 100)) for x in range(64)] for y in range(5)]
        data = wp_tga.encode(rows)
        self.assertEqual(data[16], 32)
        self.assertEqual(data[2], wp_tga.UNCOMPRESSED, 'RLE must only be chosen when it is smaller')
        self.assertEqual(wp_tga.decode(data), rows)
        mixed = [[(1, 2, 3, 255)] * 130 + [(x, x, x, 255) for x in range(130)] for _ in range(2)]
        self.assertEqual(wp_tga.decode(wp_tga.encode(mixed)), mixed, 'runs longer than 128 pixels split correctly')

    def test_read_tga_decodes_rle_packets_and_bottom_left_origin(self):
        # Two rows of three 24-bit pixels: a run packet then a literal packet,
        # stored bottom-up (no TOP_LEFT bit) so the decoder must flip the rows.
        body = bytes([0x81]) + bytes((30, 20, 10)) + bytes([0x00]) + bytes((60, 50, 40))
        body += bytes([0x02]) + bytes((1, 2, 3, 4, 5, 6, 7, 8, 9))
        data = wp_tga.header(3, 2, rle=True, top_left=False) + body
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'small.tga'
            path.write_bytes(data)
            rows = wp_tga.read_tga(path)
        self.assertEqual(rows, [[(3, 2, 1, 255), (6, 5, 4, 255), (9, 8, 7, 255)],
                                [(10, 20, 30, 255), (10, 20, 30, 255), (40, 50, 60, 255)]])

    def test_truncated_or_unsupported_images_are_errors(self):
        rows = [[(1, 2, 3)] * 8 for _ in range(2)]
        data = wp_tga.encode(rows)
        with self.assertRaises(ValueError):
            wp_tga.decode(data[:-3])
        colour_mapped = bytearray(wp_tga.header(1, 1))
        colour_mapped[2] = 1
        with self.assertRaises(ValueError):
            wp_tga.decode(bytes(colour_mapped) + b'\0\0\0')


def pivot(name, parent):
    return struct.pack('<16sI3f3f4f', name.encode(), parent & 0xFFFFFFFF, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)


def hierarchy(pivots):
    header = struct.pack('<I16sI3f', 0x40001, b'TEST', len(pivots), 0, 0, 0)
    return wp_w3d.chunk(wp_w3d.HIERARCHY, wp_w3d.chunk(wp_w3d.HIERARCHY_HEADER, header)
                        + wp_w3d.chunk(wp_w3d.PIVOTS, b''.join(pivots)), subs=True)


def hlod(bones):
    subs = b''.join(wp_w3d.chunk(wp_w3d.HLOD_SUB_OBJECT, struct.pack('<I32s', bone, wp_w3d.name32(f'TEST.M{i}')))
                    for i, bone in enumerate(bones))
    return wp_w3d.chunk(wp_w3d.HLOD,
                        wp_w3d.chunk(wp_w3d.HLOD_HEADER, struct.pack('<II16s16s', 0x10000, 1, b'TEST', b'TEST'))
                        + wp_w3d.chunk(wp_w3d.HLOD_LOD_ARRAY,
                                       wp_w3d.chunk(wp_w3d.SUB_OBJECT_ARRAY_HEADER, struct.pack('<If', len(bones), 0))
                                       + subs, subs=True), subs=True)


class HierarchyTests(unittest.TestCase):
    def pivots_of(self, data):
        body = next(p for c, s, p in wp_w3d.chunks(data) if c == wp_w3d.HIERARCHY)
        raw = next(p for c, s, p in wp_w3d.chunks(body) if c == wp_w3d.PIVOTS)
        return [(raw[i:i + 16].split(b'\0')[0].decode(), struct.unpack_from('<I', raw, i + 16)[0])
                for i in range(0, len(raw), wp_w3d.PIVOT_SIZE)]

    def bones_of(self, data):
        body = next(p for c, s, p in wp_w3d.chunks(data) if c == wp_w3d.HLOD)
        array = next(p for c, s, p in wp_w3d.chunks(body) if c == wp_w3d.HLOD_LOD_ARRAY)
        return [struct.unpack_from('<I', p)[0] for c, s, p in wp_w3d.chunks(array) if c == wp_w3d.HLOD_SUB_OBJECT]

    def test_parents_are_ordered_before_children_and_hlod_indices_follow(self):
        # CHILD is listed first (index 0) with its parent ROOT at index 1.
        data = hierarchy([pivot('CHILD', 1), pivot('ROOT', -1)]) + hlod([0, 1])
        result = w3dhierarchy.canonicalize(data)
        self.assertEqual(self.pivots_of(result), [('ROOT', wp_w3d.NO_PARENT), ('CHILD', 0)])
        self.assertEqual(self.bones_of(result), [1, 0])
        self.assertEqual(w3dhierarchy.canonicalize(result), result, 'canonical input is a fixed point')

    def test_cycles_are_rejected_and_hierarchy_free_files_pass_through(self):
        with self.assertRaises(ValueError):
            w3dhierarchy.canonicalize(hierarchy([pivot('A', 1), pivot('B', 0)]))
        plain = hlod([0])
        self.assertEqual(w3dhierarchy.canonicalize(plain), plain)

    def test_fixed_names_never_truncate_silently(self):
        self.assertEqual(len(wp_w3d.name16('A' * 15)), 16)
        with self.assertRaises(ValueError):
            wp_w3d.name16('A' * 16)
        with self.assertRaises(ValueError):
            wp_w3d.name32('B' * 32)

    def test_chunk_iterators_reject_overrun(self):
        bad = struct.pack('<II', wp_w3d.MESH, 100) + b'short'
        with self.assertRaises(ValueError):
            list(wp_w3d.chunks(bad))
        with self.assertRaises(ValueError):
            list(wp_w3d.walk(bad))


class MapReaderTests(unittest.TestCase):
    def test_truncated_reads_raise_failure_not_struct_error(self):
        reader = validate_gameplay.Reader(b'\x01\x02\x03')
        with self.assertRaises(validate_gameplay.Failure):
            reader.unpack('I')
        with self.assertRaises(validate_gameplay.Failure):
            validate_gameplay.Reader(b'\x05\x00abc').string()
        with self.assertRaises(validate_gameplay.Failure):
            validate_gameplay.Reader(b'ab').take(-1)
        self.assertNotIsInstance(validate_gameplay.Failure('x'), AssertionError)

    def test_truncated_map_files_fail_cleanly(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'broken.map'
            path.write_bytes(b'junk')
            with self.assertRaises(validate_gameplay.Failure):
                validate_gameplay.read_map(path)
            path.write_bytes(b'CkMp' + struct.pack('<i', 1) + bytes([4]) + b'Heig')  # key cut off
            with self.assertRaises(validate_gameplay.Failure):
                validate_gameplay.read_map(path)


class AmbientEmitterTests(unittest.TestCase):
    """The wind bed is a looping Limit 1 event: one neutral invisible carrier per map, never a second."""

    @staticmethod
    def decode(layout, faction, mission=None):
        name, data = genmap.generate(layout, faction, mission)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / f'{name}.map'
            path.write_bytes(data)
            return validate_gameplay.read_map(path)

    def test_generated_maps_carry_one_neutral_emitter_at_the_playable_centre(self):
        training = next(m for m in genmap.load_missions() if m['id'] == 'training')
        for layout, faction, mission in (('flats', 'meridian', None), ('range', 'jackal', None),
                                         (training['layout'], training['faction'], training)):
            game_map = self.decode(layout, faction, mission)
            validate_gameplay.ambient_emitter_placement(game_map)
            emitters = [o for o in game_map['objects'] if o['template'] == genmap.AMBIENT_EMITTER]
            width, height = game_map['terrain']['playable']
            self.assertEqual([(o['x'], o['y'], o['props']) for o in emitters],
                             [(width * 5.0, height * 5.0, {'originalOwner': 'team'})], layout)
            game_map['objects'].append(dict(emitters[0]))
            with self.assertRaisesRegex(validate_gameplay.Failure, 'exactly one'):
                validate_gameplay.ambient_emitter_placement(game_map)

    def test_a_looping_limit_one_ambient_tolerates_a_single_carrier_template(self):
        objects = validate_gameplay.blocks(ROOT / 'data/Data/INI/Default/Object.ini', 'Object')
        audio = validate_gameplay.blocks(ROOT / 'data/Data/INI/SoundEffects.ini', 'AudioEvent')
        validate_gameplay.ambient_contract(objects, audio)
        self.assertNotIn('SoundAmbient = WP_AMB_Wind', objects['WP_CommandCenter'])
        doubled = dict(objects, WP_CommandCenter=objects['WP_CommandCenter'].replace(
            '\n  Side = WP\n', '\n  SoundAmbient = WP_AMB_Wind\n  Side = WP\n', 1))
        self.assertNotEqual(doubled['WP_CommandCenter'], objects['WP_CommandCenter'])
        with self.assertRaisesRegex(validate_gameplay.Failure, 'WP_AMB_Wind'):
            validate_gameplay.ambient_contract(doubled, audio)


class GenW3dTests(unittest.TestCase):
    def test_catalog_name_collision_is_fatal_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'WPRKT01'):
                genw3d.write_models(temp, {'WPRKT01': genw3d.MODELS['WPRKT01']}, protected={'wprkt01'})
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_utility_models_and_production_catalog_are_disjoint(self):
        catalog = genw3d.catalog_models()
        self.assertIn('WPROCK01', catalog, 'the boulder prop belongs to build_polish.py')
        self.assertEqual(set(genw3d.MODELS) & catalog, set())
        self.assertNotIn('WPROCK01', genw3d.MODELS)

    def test_rocket_projectile_model_is_five_parts(self):
        with tempfile.TemporaryDirectory() as temp:
            with contextlib.redirect_stdout(io.StringIO()):
                written = genw3d.write_models(temp, {'WPRKT01': genw3d.MODELS['WPRKT01']}, genw3d.catalog_models())
            data = written[0].read_bytes()
        top = [(kind, payload) for kind, subs, payload in wp_w3d.chunks(data)]
        self.assertEqual([kind for kind, _ in top], [wp_w3d.MESH] * 5 + [wp_w3d.HLOD])
        names = [payload[8 + 8:8 + 8 + 16].split(b'\0')[0].decode() for kind, payload in top if kind == wp_w3d.MESH]
        self.assertEqual(names, ['BODY', 'NOSE', 'FINT', 'FINS', 'EXH'])
        xs = [v[0] for _, _, (verts, _, _) in genw3d.MODELS['WPRKT01'] for v in verts]
        self.assertAlmostEqual(max(xs) - min(xs), 4.25, places=6)  # exhaust tail at -2.3 to nose tip at 1.95

    def test_part_names_longer_than_the_field_are_rejected(self):
        genw3d.part('A' * 15, 'GOLD', 0, 0, 0, 1, 1, 1)
        with self.assertRaises(ValueError):
            genw3d.part('A' * 16, 'GOLD', 0, 0, 0, 1, 1, 1)


class ProjectileRuleTests(unittest.TestCase):
    INI = '''Object WP_Rocket
  KindOf = PROJECTILE ; comment
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = {rocket}
    End
  End
End

Object WP_PropRock
  KindOf = STRUCTURE
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = WPROCK01
    End
  End
End
'''

    def test_projectile_models_must_be_exclusive(self):
        shared = check_content.projectile_conflicts(self.INI.format(rocket='WPROCK01'), {'wprock01': {}})
        self.assertEqual(len(shared), 2)
        self.assertIn('WP_PropRock', shared[0])
        self.assertIn('polish_assets.json', shared[1])
        self.assertEqual(check_content.projectile_conflicts(self.INI.format(rocket='WPRKT01'), {'wprock01': {}}), [])

    def test_shipped_object_ini_has_no_projectile_conflicts(self):
        catalog = json.loads((ROOT / 'tools/blender/polish_assets.json').read_text())
        text = (ROOT / 'data/Data/INI/Default/Object.ini').read_text()
        self.assertEqual(check_content.projectile_conflicts(text, catalog), [])


class PlaceholderTests(unittest.TestCase):
    ENGINE_NAMES = ['TBBib', 'TBRedBib', 'TSCloudMed', 'TSNoiseUrb', 'exlaser', 'exmask_g', 'noise0000',
                    'tsmoonlarg', 'twalphaedge', 'twwater01', 'watersurfacebubbles']

    def test_engine_placeholders_are_solid_64px_rle_files(self):
        self.assertTrue(set(self.ENGINE_NAMES) <= set(gentex.PLACEHOLDERS))
        with tempfile.TemporaryDirectory() as temp:
            with contextlib.redirect_stdout(io.StringIO()):
                gentex.write_placeholders(Path(temp))
            for name in self.ENGINE_NAMES:
                path = Path(temp) / f'{name}.tga'
                size, rgb, alpha = gentex.PLACEHOLDERS[name]
                self.assertEqual(path.stat().st_size, 338 if alpha else 274, name)
                rows = wp_tga.read_tga(path)
                self.assertEqual((len(rows), len(rows[0])), (64, 64))
                self.assertEqual(set(p for row in rows for p in row), {rgb + (255 if alpha is None else alpha,)})


class GenMapCliTests(unittest.TestCase):
    def run_main(self, argv):
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                genmap.main(argv)
        return raised.exception.code

    def test_mission_conflicts_with_layout_and_faction(self):
        mission = genmap.load_missions()[0]['id']
        self.assertEqual(self.run_main(['--mission', mission, '--layout', 'ridge']), 2)
        self.assertEqual(self.run_main(['--mission', mission, '--faction', 'jackal']), 2)
        self.assertEqual(self.run_main(['--mission', 'no-such-mission']), 2)
        self.assertEqual(self.run_main(['--all', '--faction', 'jackal']), 2)

    def test_single_map_honours_out_and_explicit_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            with contextlib.redirect_stdout(io.StringIO()):
                genmap.main(['--layout', 'scrap', '--faction', 'jackal', '--out', str(out)])
                genmap.main(['--layout', 'scrap', '--faction', 'jackal', str(out / 'explicit.map')])
            default = out / 'WPScrapJ' / 'WPScrapJ.map'
            self.assertTrue(default.read_bytes().startswith(b'CkMp'))
            self.assertEqual(default.read_bytes(), (out / 'explicit.map').read_bytes())


if __name__ == '__main__':
    unittest.main()

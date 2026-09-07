# SPDX-License-Identifier: MIT
"""Shared setup for every headless Blender script in this directory.

Blender's ``--python`` does not put the script's own directory on ``sys.path``,
so each script starts with the two-line stub::

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _bootstrap import ROOT, register_w3d_plugin, script_args

Everything else that used to be copied between scripts lives here: the
OpenSAGE W3D exporter registration, the ``--`` argument split, and the
palette of the retained original building kits.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / 'engine/references/OpenSAGE.BlenderPlugin'

for _path in (ROOT / 'tools', ROOT / 'tools/blender', PLUGIN):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


def script_args(argv=None):
    """The arguments after Blender's ``--`` separator (empty without one)."""
    argv = sys.argv if argv is None else argv
    return argv[argv.index('--') + 1:] if '--' in argv else []


def register_w3d_plugin():
    """Register the OpenSAGE W3D importer/exporter operators once."""
    if not (PLUGIN / 'io_mesh_w3d' / '__init__.py').is_file():
        raise SystemExit(f'OpenSAGE.BlenderPlugin is missing at {PLUGIN}. It is a git submodule of the engine '
                         'checkout: run `git submodule update --init --recursive` (see tools/README.md).')
    import io_mesh_w3d
    if not hasattr(register_w3d_plugin, 'done'):
        io_mesh_w3d.register()
        register_w3d_plugin.done = True
    return io_mesh_w3d


# Palette shared by the retained original base kits (build_mercc.py,
# build_jakcp.py, build_meridian_base.py, build_jackal_base.py): linear RGBA.
KIT_PALETTE = {
    'STEEL': (0.722, 0.761, 0.800, 1.0),
    'WHITE': (0.910, 0.925, 0.941, 1.0),
    'GOLD': (0.843, 0.706, 0.353, 1.0),
    'GUN': (0.353, 0.376, 0.408, 1.0),
    'DARK': (0.290, 0.306, 0.333, 1.0),
    'TREAD': (0.200, 0.212, 0.231, 1.0),
    'GLASS': (0.18, 0.24, 0.30, 1.0),
    'SAND': (0.788, 0.690, 0.541, 1.0),
    'RUST': (0.541, 0.353, 0.235, 1.0),
    'OXIDE': (0.435, 0.561, 0.353, 1.0),
    'GRAPHITE': (0.290, 0.306, 0.333, 1.0),
    'CHARCOAL': (0.180, 0.192, 0.220, 1.0),
}


def kit_output_dirs(argv=None, default_data=None):
    """``--data DIR`` (models under Art/W3D, textures under Art/Textures) or
    ``--scratch DIR`` (one flat review directory) for the retained kits."""
    import argparse
    parser = argparse.ArgumentParser(description='Retained original building kit; run through Blender: '
                                     'blender --background --factory-startup --python <script> -- [--data DIR | --scratch DIR]')
    parser.add_argument('--data', type=Path, default=default_data or ROOT / 'data',
                        help='dataset root (default: the repository data/)')
    parser.add_argument('--scratch', type=Path, help='explicit flat review directory for models and textures')
    args = parser.parse_args(script_args(argv))
    model_dir = args.scratch or args.data / 'Art/W3D'
    texture_dir = args.scratch or args.data / 'Art/Textures'
    for path in (model_dir, texture_dir):
        path.mkdir(parents=True, exist_ok=True)
    return str(model_dir), str(texture_dir)



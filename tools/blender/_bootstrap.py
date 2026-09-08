# SPDX-License-Identifier: MIT
"""Shared setup for every headless Blender script in this directory.

Blender's ``--python`` does not put the script's own directory on ``sys.path``,
so each script starts with the two-line stub::

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _bootstrap import ROOT, register_w3d_plugin, script_args

Everything else that used to be copied between scripts lives here: the
OpenSAGE W3D exporter registration and the ``--`` argument split.
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



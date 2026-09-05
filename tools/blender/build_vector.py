"""Build the original Vector with turret, muzzle and player-color geometry.

Compatibility command: blender --background --python tools/blender/build_vector.py
Optional arguments after -- are forwarded to build_polish.py (for example --data data).
No external meshes are loaded.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_polish import main

if __name__=='__main__':
    if '--' not in sys.argv:sys.argv.append('--')
    if '--only' not in sys.argv:sys.argv.extend(['--only','mertank01'])
    main()

# Asset Provenance Ledger

Every asset file that enters the project gets a row **when it is added, not later**. This ledger is what lets us ship legally and publicly without an audit crisis.

**Acceptance rules (from decisions D007/D009):**
- ✅ Original work (ours) — licensed CC BY-SA 4.0 on release
- ✅ CC0 / public domain
- ✅ CC-BY / CC-BY-SA (attribution tracked here, credited in-game)
- ❌ Anything EA-derived, anything NC/ND-encumbered, anything unlicensed

| Path | What | Source | Author | License | Added | Notes |
|---|---|---|---|---|---|---|
| data/Data/Audio/Tracks/wp_ambient_01.mp3 | 12s ambient tone loop (A2+E3 sine mix) | Original — generated via ffmpeg | War Powers project | CC BY-SA 4.0 (ours) | 2026-08-21 | Satisfies the engine's ≥1-music-file boot gate |
| data/Art/Textures/wp_water.tga | 32×32 solid deep-teal water texture | Original — generated | War Powers project | CC BY-SA 4.0 (ours) | 2026-08-21 | Placeholder for WaterSet blocks |
| data/Art/Textures/wp_sky.tga | 32×32 solid hazy-sky texture | Original — generated | War Powers project | CC BY-SA 4.0 (ours) | 2026-08-21 | Placeholder for WaterSet blocks |
| data/Art/W3D/*.w3d (wpcc01, wptank01) | Generated box models (tools/genw3d.py) | Original — generated | War Powers project | CC BY-SA 4.0 (ours) | 2026-08-21 | Boot Slice placeholders |
| data/Art/Textures/wp_box.tga + 13 placeholder TGAs | Generated placeholder textures | Original — generated | War Powers project | CC BY-SA 4.0 (ours) | 2026-08-21 | Terrain/water/effects/test stages |
| data/Data/** + data/Window/** | ~70 INI/WND text files | Original — authored against engine's documented formats | War Powers project | GPL-compatible (engine-config; WND structure derived from GeneralsX's GPL ExtrasMenu.wnd example) | 2026-08-21 | The zero-retail boot dataset |
| data/Data/Generals.str | UI strings (hand-authored) | Original — authored | War Powers project | CC BY-SA 4.0 (ours) | 2026-08-22 | Boot Slice UI text |
| data/Fonts/LiberationSans-Regular.ttf | Liberation Sans 2.1.5 | Third-party — Red Hat/liberationfonts | github.com/liberationfonts | SIL OFL 1.1 (license file alongside) | 2026-08-22 | Web build UI font (fontconfig stub target) |
| data/Art/W3D/mertank01.w3d + Textures/wp_vector.tga | Hero Vector MBT (Blender-scripted, baked AO texture) | Original — tools/blender/build_vector.py | War Powers project | CC BY-SA 4.0 (ours) | 2026-08-22 | D015 hero asset v1; supersedes part-language placeholder |
| refs/quaternius-tanks/*.fbx | Source pack: 4 low-poly tanks + preview | Third-party — quaternius.com "Tanks" pack | Quaternius | CC0 1.0 (License.txt alongside) | 2026-08-22 | Conversion sources only; not shipped directly |
| data/Art/W3D/jaktank01.w3d + Textures/wp_mongrel.tga | Jackal Mongrel tank (converted Quaternius Tank3: retint to Jackal palette, re-UV, baked AO texture) | Adapted from CC0 — tools/blender/convert_mongrel.py | Quaternius (base mesh) / War Powers project (adaptation) | CC BY-SA 4.0 (adaptation of CC0) | 2026-08-22 | D015 pack-conversion spike; supersedes part-language placeholder |

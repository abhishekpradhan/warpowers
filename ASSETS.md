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

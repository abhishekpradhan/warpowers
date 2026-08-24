# Asset Provenance Ledger

Every asset file that enters the project gets a row **when it is added, not later**. This ledger is what lets us ship legally and publicly without an audit crisis.

**Acceptance rules (D019 — legality is the only bar; per-file licensing):**
- ✅ Original work (ours) — CC BY 4.0
- ✅ CC0 / public domain (adaptations ship under our CC BY 4.0)
- ✅ CC-BY / CC-BY-SA / GPL-licensed art / OFL — the file (and adaptations,
  where the license requires) ships under its upstream license; this ledger
  is the authoritative per-file license map, CREDITS.md carries the credits
- ⚠️ NC only by explicit per-case decision noted here (permanently bars
  commercial use of that asset)
- ❌ Anything EA-derived (unlicensed derivative works), anything unlicensed,
  ND-encumbered (the style pipeline modifies everything; ND bars derivatives)

| Path | What | Source | Author | License | Added | Notes |
|---|---|---|---|---|---|---|
| data/Data/Audio/Tracks/wp_ambient_01.mp3 | 12s ambient tone loop (A2+E3 sine mix) | Original — generated via ffmpeg | War Powers project | CC BY 4.0 (ours) | 2026-08-21 | Satisfies the engine's ≥1-music-file boot gate |
| data/Art/Textures/wp_water.tga | 32×32 solid deep-teal water texture | Original — generated | War Powers project | CC BY 4.0 (ours) | 2026-08-21 | Placeholder for WaterSet blocks |
| data/Art/Textures/wp_sky.tga | 32×32 solid hazy-sky texture | Original — generated | War Powers project | CC BY 4.0 (ours) | 2026-08-21 | Placeholder for WaterSet blocks |
| data/Art/W3D/*.w3d (wpcc01, wptank01) | Generated box models (tools/genw3d.py) | Original — generated | War Powers project | CC BY 4.0 (ours) | 2026-08-21 | Boot Slice placeholders |
| data/Art/Textures/wp_box.tga + 13 placeholder TGAs | Generated placeholder textures | Original — generated | War Powers project | CC BY 4.0 (ours) | 2026-08-21 | Terrain/water/effects/test stages |
| data/Data/** + data/Window/** | ~70 INI/WND text files | Original — authored against engine's documented formats | War Powers project | CC BY 4.0 (ours; WND file *format* learned from the engine's GPL example — formats aren't copyrightable, content is original) | 2026-08-21 | The zero-retail boot dataset |
| data/Data/Generals.str | UI strings (hand-authored) | Original — authored | War Powers project | CC BY 4.0 (ours) | 2026-08-22 | Boot Slice UI text |
| data/Fonts/LiberationSans-Regular.ttf | Liberation Sans 2.1.5 | Third-party — Red Hat/liberationfonts | github.com/liberationfonts | SIL OFL 1.1 (license file alongside) | 2026-08-22 | Web build UI font (fontconfig stub target) |
| data/Art/W3D/mertank01.w3d + Textures/wp_vector.tga | Hero Vector MBT (Blender-scripted, baked AO texture) | Original — tools/blender/build_vector.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 | D015 hero asset v1; supersedes part-language placeholder |
| refs/quaternius-tanks/*.fbx | Source pack: 4 low-poly tanks + preview | Third-party — quaternius.com "Tanks" pack | Quaternius | CC0 1.0 (License.txt alongside) | 2026-08-22 | Conversion sources only; not shipped directly |
| data/Art/W3D/jaktank01.w3d + Textures/wp_mongrel.tga | Jackal Mongrel tank (converted Quaternius Tank3: retint to Jackal palette, re-UV, baked AO texture) | Adapted from CC0 — tools/blender/convert_mongrel.py | Quaternius (base mesh) / War Powers project (adaptation) | CC BY 4.0 (adaptation of CC0) | 2026-08-22 | D015 pack-conversion spike; supersedes part-language placeholder |
| data/Art/W3D/mercc01.w3d + Textures/wp_mercc.tga | Meridian Command Center (Blender-scripted architecture, baked texture) | Original — tools/blender/build_mercc.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 | D015 hero building; supersedes part-language placeholder |
| data/Art/W3D/jakcp01.w3d + Textures/wp_jakcp.tga | Jackal Command Post (Blender-scripted architecture, baked texture) | Original — tools/blender/build_jakcp.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 | D015 hero building; supersedes part-language placeholder |
| data/Art/W3D/wpshell01.w3d | Tank shell tracer model | Original — tools/genw3d.py | War Powers project | CC BY 4.0 (ours) | 2026-08-23 | Projectile for WP_TankGun |
| data/Art/Textures/EXScorch01.tga | Terrain scorch atlas (4 marks) | Original — tools/gentex.py | War Powers project | CC BY 4.0 (ours) | 2026-08-23 | Filename hardcoded by engine; art is ours |
| data/Data/Audio/Sounds/*.wav (20 files) | SFX (cannon/impact/boom) + unit VO radio barks | Original — tools/gensfx.py (DSP + eSpeak NG synthesis) | War Powers project | CC BY 4.0 (ours) | 2026-08-23 | eSpeak NG output is unencumbered; D014 processed-radio direction |

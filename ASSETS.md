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
| data/Data/Audio/Tracks/wp_ambient_01.mp3 | 12s ambient tone loop (A2+E3 sine mix) | Original — generated via ffmpeg | War Powers project | CC BY 4.0 (ours) | 2026-08-21 | REMOVED 2026-08-30, replaced by the 6-track music rotation below (row kept for history) |
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
| data/Art/W3D/merout01.w3d + Textures/wp_outrider.tga | Meridian Outrider recon (converted Quaternius Tank2: retint, re-UV, baked) | Adapted from CC0 — tools/blender/convert_pack_units.py | Quaternius (base mesh) / War Powers project (adaptation) | CC BY 4.0 (adaptation of CC0) | 2026-08-24 | Pack-conversion batch 2 (row added 2026-08-31 ledger sweep) |
| data/Art/W3D/jakvul01.w3d + Textures/wp_vulture.tga | Jackal Vulture gun truck (converted Quaternius Tank: retint, re-UV, baked) | Adapted from CC0 — tools/blender/convert_pack_units.py | Quaternius (base mesh) / War Powers project (adaptation) | CC BY 4.0 (adaptation of CC0) | 2026-08-24 | Pack-conversion batch 2 (row added 2026-08-31 ledger sweep) |
| data/Art/W3D/merzen01.w3d + Textures/wp_zenith.tga | Meridian Zenith artillery (converted Quaternius Tank4: retint, re-UV, baked) | Adapted from CC0 — tools/blender/convert_pack_units.py | Quaternius (base mesh) / War Powers project (adaptation) | CC BY 4.0 (adaptation of CC0) | 2026-08-24 | Pack-conversion batch 2 (row added 2026-08-31 ledger sweep) |
| data/Art/W3D/*.w3d (54 models) + data/Art/Textures/wp_*.tga | All other unit/structure/effect models + painted textures | Original — tools/blender/build_*.py + wp_pipeline.py, tools/genw3d.py, tools/gentex.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 → ongoing | Everything not listed as an adaptation above is scripted from scratch; glob row per D019 |
| data/Maps/* (10 maps) | Skirmish map set (layouts × biomes) | Original — tools/genmap.py | War Powers project | CC BY 4.0 (ours) | 2026-08-24 → ongoing | Fully generated; regenerate, never hand-edit |
| data/Window/** + icon/portrait sheets | WND layouts, command icons, unit portraits | Original — tools/genwnd.py, genicons2.py, gencmdicons.py, genportraitsheet.py (Blender portrait renders) | War Powers project | CC BY 4.0 (ours) | 2026-08-22 → ongoing | Glob row per D019 |
| data/Art/W3D/mercc01.w3d + Textures/wp_mercc.tga | Meridian Command Center (Blender-scripted architecture, baked texture) | Original — tools/blender/build_mercc.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 | D015 hero building; supersedes part-language placeholder |
| data/Art/W3D/jakcp01.w3d + Textures/wp_jakcp.tga | Jackal Command Post (Blender-scripted architecture, baked texture) | Original — tools/blender/build_jakcp.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 | D015 hero building; supersedes part-language placeholder |
| data/Art/W3D/wpshell01.w3d | Tank shell tracer model | Original — tools/genw3d.py | War Powers project | CC BY 4.0 (ours) | 2026-08-23 | Projectile for WP_TankGun |
| data/Art/Textures/EXScorch01.tga | Terrain scorch atlas (4 marks) | Original — tools/gentex.py | War Powers project | CC BY 4.0 (ours) | 2026-08-23 | Filename hardcoded by engine; art is ours |
| data/Data/Audio/Sounds/*.wav (191 files, grows with roster) | SFX (weapons/impacts/ambience beds) + unit VO radio barks | Original — tools/gensfx.py (DSP + eSpeak NG synthesis) | War Powers project | CC BY 4.0 (ours) | 2026-08-23 → ongoing | eSpeak NG output is unencumbered; D014 processed-radio direction |

## Music (imported, CC BY 4.0)

| File | Track | Author | Source | License | Modifications |
|---|---|---|---|---|---|
| data/Data/Audio/Tracks/volatile_reaction.mp3 | "Volatile Reaction" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/interloper.mp3 | "Interloper" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/crypto.mp3 | "Crypto" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/rites.mp3 | "Rites" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/mechanolith.mp3 | "Mechanolith" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/stormfront.mp3 | "Stormfront" | Kevin MacLeod | incompetech.com | CC BY 4.0 | trimmed to 4:30 + fade, re-encoded 96kbps |

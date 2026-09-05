# Asset Provenance Ledger

This ledger records the declared provenance and license of shipped content. Add a row when introducing an asset family and update it when a production replacement changes its source. The generated `data/asset-registry.json` supplies the current per-model inventory; `tools/blender/polish_assets.json` records production model contracts.

**Acceptance rules (D019 as narrowed by D022 — legality is the exclusion
bar; per-file licensing; permissive-attribution imports only):**
- ✅ Original work (ours) — CC BY 4.0
- ✅ CC0 / public domain (adaptations ship under our CC BY 4.0)
- ✅ CC BY / SIL OFL — the file ships under its upstream license; this
  ledger is the authoritative per-file license map, CREDITS.md the credits
- ⚠️ ShareAlike / GPL art / NC: not pre-approved — each would need a fresh
  decision-log entry before import (none ever has)
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
| data/Art/W3D/mertank01.w3d + Textures/wp_vector.tga | Vector MBT, articulated turret and ownership panel | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22; rebuilt 2026-09-05 | Original beveled geometry, painted AO atlas; TURRET → BARREL → MUZZLE recoil hierarchy; supersedes the earlier build_vector.py model |
| refs/quaternius-tanks/*.fbx | Source pack: 4 low-poly tanks + preview | Third-party — quaternius.com "Tanks" pack | Quaternius | CC0 1.0 (License.txt alongside) | 2026-08-22 | Historical conversion sources only; current production scripts do not import them and they are not staged |
| data/Art/W3D/jaktank01.w3d + Textures/wp_mongrel.tga | Mongrel tracked tank | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | Replaced 2026-09-05 | Original asymmetric chassis and turret; retired the 2026-08-22 Quaternius Tank3 adaptation |
| data/Art/W3D/merout01.w3d + Textures/wp_outrider.tga | Outrider wheeled recon car | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | Replaced 2026-09-05 | Original low armored four-wheel silhouette; retired the 2026-08-24 Quaternius Tank2 adaptation |
| data/Art/W3D/jakvul01.w3d + Textures/wp_vulture.tga | Vulture open-bed gun pickup | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | Replaced 2026-09-05 | Original cab, roll cage, bed and pedestal gun; retired the 2026-08-24 Quaternius Tank adaptation |
| data/Art/W3D/merzen01.w3d + Textures/wp_zenith.tga | Zenith six-wheel siege carrier | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | Replaced 2026-09-05 | Original siege chassis and articulated gun; retired the 2026-08-24 Quaternius Tank4 adaptation |
| data/Art/W3D/*.w3d (remaining models) + data/Art/Textures/wp_*.tga | All other unit/structure/effect models + painted textures | Original — tools/blender/build_*.py + wp_pipeline.py, tools/genw3d.py, tools/gentex.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 → ongoing | Retained original base architecture and builders, projectiles, scaffolds and historical unused boot models. Active roster aircraft/support models now have explicit production rows below; glob row per D019 |
| data/Maps/* | Skirmish layouts, training, operations and challenge maps | Original — tools/genmap.py | War Powers project | CC BY 4.0 (ours) | 2026-08-24 → ongoing | Fully generated; regenerate, never hand-edit |
| data/Window/** + icon/portrait sheets | WND layouts, command icons, unit portraits | Original — tools/genwnd.py, gencmdicons.py, tools/blender/render_roster.py, genportraitsheet.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 → ongoing | Glob row per D019 |
| data/Art/W3D/mercc01.w3d + Textures/wp_mercc.tga | Meridian Command Center (Blender-scripted architecture, baked texture) | Original — tools/blender/build_mercc.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 | D015 hero building; supersedes part-language placeholder |
| data/Art/W3D/jakcp01.w3d + Textures/wp_jakcp.tga | Jackal Command Post (Blender-scripted architecture, baked texture) | Original — tools/blender/build_jakcp.py | War Powers project | CC BY 4.0 (ours) | 2026-08-22 | D015 hero building; supersedes part-language placeholder |
| data/Art/W3D/wpshell01.w3d | Tank shell tracer model | Original — tools/genw3d.py | War Powers project | CC BY 4.0 (ours) | 2026-08-23 | Projectile for WP_TankGun |
| data/Art/Textures/EXScorch01.tga | Terrain scorch atlas (4 marks) | Original — tools/gentex.py | War Powers project | CC BY 4.0 (ours) | 2026-08-23 | Filename hardcoded by engine; art is ours |
| data/Data/Audio/Sounds/*.wav (205 files at this pass) | SFX (weapons/impacts/ambience beds) + unit VO radio barks | Original — tools/gensfx.py (DSP + eSpeak NG synthesis) | War Powers project | CC BY 4.0 (ours) | 2026-08-23 → ongoing | DSP synthesis and eSpeak NG radio processing; D014 direction. Includes 14 dedicated Porter/Scavenger lines; deterministic per-file DSP seeds |

| data/Art/W3D/{merhaul01,jakhaul01}.w3d + Textures/wp_{porter,scavenger}.tga | Dedicated supply haulers with cargo mesh | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | 2026-09-05 | Separate HULL/CARGO, six wheel pivots and ownership panel; native cargo visibility and wheel movement |
| data/Art/W3D/{mer,jak}{inf02,roc01,sct01,hvy01}.w3d + Textures/wp_{warden,scrapper,lancer,sting,vigil,prowler,bastion,bruiser}.tga | Eight armored infantry models | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | Replaced 2026-09-05 | Authored armor, equipment and role silhouettes; shared WPINF1 skeleton, 256px painted atlases, ownership panel |
| data/Art/W3D/wpinf1*.w3d | Shared infantry skeleton, idle/walk/fire/death clips | Original — tools/genrig.py | War Powers project | CC BY 4.0 (ours) | 2026-08-24; death added 2026-09-05 | Rigid eight-bone animation; 28-frame death clip at 24fps. Generator no longer replaces finished infantry bodies |
| data/Art/W3D/{wprock01,wpscrap01,wprelay01,wpwall01}.w3d + Textures/wp_{rock,scrap,relay,wall}.tga | Neutral rock, supply scrap, communications relay and barrier kit | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | 2026-09-05 | Shared battlefield palette; 128px rock/barrier and 256px supply/relay atlases; authored from primitives without external geometry |
| data/Art/W3D/{mertank01d,jaktank01d,merout01d,jakvul01d,merzen01d}.w3d + Textures/wp_{vector,mongrel,outrider,vulture,zenith}_d.tga | Five damaged combat vehicle variants | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | 2026-09-05 | Darkened/scorched material treatment, 256px atlases; retains turret, muzzle and ownership. Matching native recoil and wheeled pivots; no component break-off animation |
| data/Art/W3D/{wpwreck01,wpwreck02,wpruin01,wpruin02}.w3d + Textures/wp_{merwreck,jakwreck,ruinlarge,ruinsmall}.tga | Faction wrecks and two structure rubble sizes | Original — tools/blender/build_polish.py | War Powers project | CC BY 4.0 (ours) | 2026-09-05 | Deformed tracked chassis and authored broken masonry/debris. Generic remains shared across roles, not a bespoke wreck for every unit |
| data/Art/Textures/wp_cmdicons{,2}.tga + MappedImages/HandCreated/WPCmdIcons{,2}.ini | 44 consistent unit, building, ability and objective portraits | Original — tools/blender/render_roster.py + tools/genportraitsheet.py | War Powers project | CC BY 4.0 (ours) | Rebuilt 2026-09-05 | Actual shipped models rendered with one camera/light setup; original ability diagrams. Old genicons2 entry point now packs rendered portraits |
| data/Art/Textures/wp_menu.tga + MappedImages/HandCreated/WPMenuArt.ini | Main-menu battlefield panorama | Original — tools/blender/render_menu.py | War Powers project | CC BY 4.0 (ours) | 2026-09-05 | Scene composed from the original production kit; 910×512 crop inside 1024×512 atlas; unused side padding is solid for compact storage; no raster lettering |
| data/Art/Textures/wp_map_previews.tga + MappedImages/HandCreated/WPMapPreviews.ini | Five tactical deployment previews | Original — tools/gentactical.py | War Powers project | CC BY 4.0 (ours) | 2026-09-05 | Derived from actual map height and object data, 256×192 per layout |

| data/Art/W3D/{merjet01,merjet02,jakjet01,jakjet02}.w3d + Textures/wp_{kestrel,shrike,buzzard,gnat}.tga | Four distinct aircraft | Original — tools/blender/support_kit.py via build_polish.py | War Powers project | CC BY 4.0 (ours) | Replaced 2026-09-05 | Ducted attack VTOL, swept-wing strafer, tandem-rotor gunship and quad-duct drone; 256px painted skins and ownership panels. Rotor blades remain static |
| data/Art/W3D/{merpad01,jakpad01,merex01,jakex01,mertech01,jaktech01,jakpwr01}.w3d + Textures/wp_{launchpad,roost,exchange,racket,directorate,den,dynamo}.tga | Airfields, loading depots, technology buildings and Dynamo | Original — tools/blender/support_kit.py via build_polish.py | War Powers project | CC BY 4.0 (ours) | Replaced 2026-09-05 | Original architectural silhouettes, painted 256px atlases, roof equipment and ownership panels |
| data/Art/W3D/{meraa01,jakaa01,merpill01,jakpill01,merart01,jakart01,merbul01,jakwp01}.w3d + Textures/wp_{skyspear,flakhut,rampart,nest,longbow,lobber,bulwark,watchpost}.tga | Eight defense structures | Original — tools/blender/support_kit.py via build_polish.py | War Powers project | CC BY 4.0 (ours) | Replaced/rebuilt 2026-09-05 | Original painted emplacements; AA/artillery/Bulwark/Watchpost have actual native turret and muzzle pivots; pillbox guns remain fixed |
| data/Art/W3D/{mercc01,jakcp01,merpp01,merwf01,jakcs01,mersuv01,jakrig01}.w3d | Ownership finish on retained original base kit | Original — existing build scripts + tools/blender/legacy_contracts.py | War Powers project | CC BY 4.0 (ours) | Updated 2026-09-05 | Original base geometry retained; independent HOUSECOLOR panels added idempotently; atlases standardized at 256px |

## Music (imported, CC BY 4.0)

| File | Track | Author | Source | License | Modifications |
|---|---|---|---|---|---|
| data/Data/Audio/Tracks/volatile_reaction.mp3 | "Volatile Reaction" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/interloper.mp3 | "Interloper" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/crypto.mp3 | "Crypto" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/rites.mp3 | "Rites" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/mechanolith.mp3 | "Mechanolith" | Kevin MacLeod | incompetech.com | CC BY 4.0 | re-encoded 96kbps |
| data/Data/Audio/Tracks/stormfront.mp3 | "Stormfront" | Kevin MacLeod | incompetech.com | CC BY 4.0 | trimmed to 4:30 + fade, re-encoded 96kbps |

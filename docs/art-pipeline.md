# Art production and runtime contracts

The September 2026 pass replaces the four borrowed runtime vehicle models with original geometry and establishes one repeatable treatment for vehicles, infantry, scenery and portraits. The production catalog is `tools/blender/polish_assets.json`; `data/asset-registry.json` inventories all shipped W3Ds. A catalog entry means this pipeline produced the model, not that every product-quality concern is finished.

All new geometry in `build_polish.py` and `support_kit.py` is authored from primitives. Every active roster unit and structure now has an original painted model; seven established base/builder designs retain their architecture with new ownership panels. The Quaternius files under `refs/` remain historical references and are not loaded by the current build. Music and fonts retain their separate attribution requirements in `ASSETS.md` and `CREDITS.md`.

## Rebuild

Use Blender 5.2 and the repository's `engine/references/OpenSAGE.BlenderPlugin` checkout. The modeling, UV, Cycles diffuse/AO/mask bake, painted composite and W3D export are scripted. Seeds are fixed. Pixel-perfect equality across Blender or render-device versions is not promised.

```sh
python3 tools/genrig.py data/Art/W3D
blender --background --factory-startup --python tools/blender/build_polish.py -- --data data --review /tmp/warpowers-art-review
blender --background --factory-startup --python tools/blender/render_roster.py -- --data data --out /tmp/warpowers-portraits
python3 tools/genportraitsheet.py /tmp/warpowers-portraits --data data
blender --background --factory-startup --python tools/blender/render_menu.py -- --data data
python3 tools/gentactical.py --data data
python3 tools/optimize_art.py --data data
python3 tools/check_content.py --write-registry
```

On macOS the installed executable may be `/Applications/Blender.app/Contents/MacOS/Blender`. `build_polish.py --only merout01,jakvul01` rebuilds a bounded set. `--catalog-only` refreshes metadata from existing files. Output defaults point to repository `data/`; use an explicit `--data /tmp/...` for a separate asset tree. Scratch exports do not change the tracked catalog. Render output and review contacts live outside the release tree.

The retained original building kits (`build_mercc.py`, `build_jakcp.py`, `build_meridian_base.py`, `build_jackal_base.py`) use `--data` for normal outputs or `--scratch` for an explicitly selected flat review directory. The historical Vector and pack-conversion entry points forward to the original production generator. `genw3d.py` skips every model in the production catalog; `genrig.py` owns skeleton/animation files only. `genicons2.py` forwards to the rendered portrait packer and cannot regenerate the retired drawing placeholders. Texture/glyph generators accept `--data` or explicit paths. No asset generator implicitly writes to a native game install in the user's home directory.

## Geometry and ownership

| Models | Runtime contract | Current coverage |
|---|---|---|
| MERTANK01, JAKTANK01, MEROUT01, JAKVUL01, MERZEN01 | HULL, TURRET, BARREL, MUZZLE, HOUSECOLOR0 | Native turret, recoil barrel and player-colored surface; wheeled vehicles add wheel pivots |
| Those five IDs plus D | Same turret/barrel/muzzle/ownership contract | Damaged and really-damaged material variant; original silhouette retained |
| MERHAUL01, JAKHAUL01 | HULL, CARGO, WHL/WHR_F/M/R, HOUSECOLOR0 | Loaded/empty cargo visibility through CARRYING and six moving wheels |
| MER/JAK INF02, ROC01, SCT01, HVY01 | WPINF1 shared skeleton; torso-bound HOUSECOLOR0 | Idle, movement, fire and death; eight armored role silhouettes |
| MER/JAK JET01 and JET02 | Separate original airframes and HOUSECOLOR0 | Four role silhouettes, 256px painted skins; static rotor blades |
| MER/JAK AA01, ART01; MERBUL01, JAKWP01 | TURRET, MUZZLE, HOUSECOLOR0 | Native aiming and weapon origin |
| Airpads, economy, tech, pillboxes and Dynamo | Original painted HLOD and HOUSECOLOR0 | Role-specific architecture, 256px atlas per model |
| Retained HQs, production/power buildings and builders | Original painted HLOD and HOUSECOLOR0 | Idempotent ownership panels from legacy_contracts.py |
| WPROCK01, WPSCRAP01, WPRELAY01, WPWALL01 | Static painted HLOD | Rock, supplies/scrap, relay and barrier set dressing |
| WPWRECK01, WPWRECK02 | Static, deformed faction chassis | Generic wrecks shared by several ground vehicles |
| WPRUIN01, WPRUIN02 | Static broken masonry/debris | Large/small generic building remains |

Units face +X. Pivot translations and mesh positions must agree: vehicles use their authored turret center; infantry preserve the existing WPINF1 indices. The engine recognizes meshes whose base name begins `HOUSECOLOR` and recolors their vertex material to the owning player. These panels are separate original geometry; do not bake player identity into a fixed faction-color texture. Wheel meshes use WHL_F/WHR_F, WHL_R/WHR_R and WHL_M/WHR_M on six-wheel chassis. Native W3DTruckDraw needs FOUR_WHEELS locomotor appearance to provide wheel rotation/suspension state. Recoil uses BARREL beneath TURRET and MUZZLE beneath BARREL, with local +X along the bore. `tools/w3dhierarchy.py` topologically orders pivots and remaps HLOD indices so both the engine and Blender importer see each parent before its children. Native draw declarations belong in `data/Data/INI/Default/Object.ini`.

WPINF1DIE is 28 frames at 24 fps (about 1.17 seconds). Infantry have a 1.8-second SlowDeath window to play and settle. Wrecks/rubble use InactiveBody, NO_COLLIDE and a 60-second lifetime; unfinished buildings are exempt from spawning ruins. The scene remains readable and these decorative leftovers do not block paths.

## Material and image budgets

Meridian uses steel/ivory with restrained gold accents; Jackal uses sand/rust with olive accents. Dark undercarriage and glass separate mechanical volumes. The composite adds AO, subtle grain, edge wear and low-frequency color variation. Vector and Mongrel retain 512×512 painted atlases. All other active roster models, retained base buildings and lifecycle variants use 256×256. Rock/barrier props use128×128; supply scrap and relays use256×256. Optimize for recognition at the actual RTS camera distance before adding texture detail.

The 44 command portraits use the shipped models, one orthographic camera, a common studio light setup and restrained faction plates. Ability portraits are original rendered diagrams. The main panorama uses the original model kit, with quieter ground on the left for native typography and action on the right. `WPMenuBackdrop` maps the 910×512 center crop within a 1024×512 TGA to the native 16:9 canvas. The tactical sheet contains five 256×192 previews derived from actual map height and object data; regenerate it after map generation.

`optimize_art.py` removes fully opaque alpha and uses TGA RLE only when smaller. Every rewritten file is decoded and compared to its pre-encoding RGBA pixels. The explicit compact-atlas list also area-reduces old 512px exports to the current 256px source contract; those source-contract reductions are the only changes to visible pixel content. The unused57px margins outside the menu image's910px crop are replaced by solid padding for compact storage. Run optimization after rendering/baking, before staging. Keep the existing 64 MiB combined browser bundle budget; do not raise it to accommodate redundant image precision.

## Audio

```sh
python3 tools/gensfx.py --data data
python3 tools/gensfx.py --data data --only-prefix wp_por,wp_scv
```

The pack combines DSP weapon/impact sounds with eSpeak NG speech passed through the project's radio chain. Every filename gets a stable character-derived seed, so Python's process-randomized hash does not change the DSP noise on each run. eSpeak's own speech synthesis may still vary slightly between invocations; this is not a claim of byte-identical voice exports. A second audio destination is opt-in with `--runtime /explicit/path`. Porter and Scavenger have separate Select/Move/Ready lines and SoundEffects events. These are still synthetic performances; the consistent processing and writing do not substitute for performance direction or a final listening/mix review.

## Review and remaining work

Run the content validator for model/texture references and triangle ceilings, and the gameplay/voice checks before staging. Inspect rendered contacts for silhouettes, detached components, UV seams and dark surfaces. In the game check turret aiming, muzzle origin, player-color readability, loaded trucks, infantry movement/death, damaged units and remains. Verify the native menu crop and portrait legibility at the smallest supported viewport. A successful export or file count is not a visual review.

All 41 roster portraits now reference original painted unit/structure models, including four distinct aircraft and 15 support/defense replacements. Seven established base/builder designs retain their original architecture with the ownership finish. This does not make a static render a gameplay approval. Building construction still uses generic scaffolds; wrecks are faction-level shared assets; infantry use rigid shared motion; aircraft rotors and tank treads remain static. Wheels and recoil have native runtime bindings, but their behavior needs camera-distance review. Damage mostly changes materials rather than breaking components. Bespoke structure destruction, richer terrain transitions, weapon impact effects, final audio mixing and broader playtests remain product polish work.

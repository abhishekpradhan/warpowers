# Engine notes — running the GeneralsX/ZH engine on the War Powers dataset

Durable knowledge about the engine fork in `engine/` (the Zero Hour build is
the `GeneralsMD/` tree, target `z_generals` → `GeneralsXZH`; shared code in
`Core/`) and about what a zero-retail dataset must provide for it to boot,
render and play. The dated bring-up log that produced these findings is in
[history/engine-log-2026-08.md](history/engine-log-2026-08.md); the browser
shell ↔ engine contract is in [web-bridge.md](web-bridge.md); the diagnostic
harness is in [testing.md](testing.md).

## The minimal dataset

1. **About 46 must-exist INI paths.** The engine hard-dies
   (`throw INI_CANT_OPEN_FILE` → `RELEASE_CRASH`) on any missing one, but
   shrugs at dangling references inside them (all cross-reference validators
   are no-ops in release). Each `Data\INI\X` demand is satisfied by
   `Data/INI/X.ini` *or* any `.ini` inside `Data/INI/X/`. The authored set is
   `data/Data/INI/**`.
2. **Exactly one must-exist binary asset:** at least one music file. The
   engine silently sets `quitting` if no `MusicTrack` resolves to a file on
   disk (`AudioSettings.AudioRoot\MusicFolder\Filename`).
3. **A handful of must-exist WND layouts** whose absence is a null-deref, not
   a clean error: `Menus/MainMenu.wnd`, `Menus/BlankWindow.wnd`,
   `ControlBar.wnd` (plus every named child the code looks up),
   `GeneralsExpPoints.wnd`, `ControlBarPopupDescription.wnd`,
   `ReplayControl.wnd`. A missing WND *file* makes `winCreateFromScript`
   return null harmlessly; a missing named *window* crashes at the unguarded
   lookup.

Everything visual degrades gracefully: missing W3D model → invisible object;
missing texture → magenta placeholder; missing shader → logged error; missing
CSF/STR string → raw label.

## Loading and resolution

- **Loose files beat archives; archives are optional.** `StdBIGFileSystem`
  mounts every `*.big` it finds but boots happily with none. Ship everything
  loose.
- **Asset root resolution**, in order: `$CNC_GENERALS_ZH_PATH` →
  `$GENERALSX_ASSET_PATH` → `$CNC_ZH_INSTALLPATH` → `Options.ini [Paths]` →
  `registry.ini` → `<exedir>/../Resources` → `<exedir>` → current directory.
  The browser page sets the environment variable and `chdir`s to `/game`.
- **User data directory** (saves, user maps, `registry.ini`): on macOS
  `Library/Application Support/GeneralsX/GeneralsZH/` under the home
  directory; in the browser a synthetic directory backed by IDBFS. User maps
  are disk-scanned; asset-root `Maps/` needs `MapCache.ini` unless
  `-buildmapcache` (patched into release on this fork).
- **Language** resolves to `english` through the port's `registry.ini`
  default; `Data/english/` holds Language, HeaderTemplate and CommandMap.
- **MEMFS is case-sensitive where macOS was not.** The page symlinks
  `/game/data` → `/game/Data`; keep dataset paths consistently cased.
- **`Generals.str` is read as ANSI.** UTF-8 typographic characters mojibake
  in-game; keep the string table pure ASCII.
- **Release-build flags:** `-win -fullscreen -headless -xres -yres
  -noshellmap -noShellAnim -nologo -quickstart -mod -noshaders`, plus this
  fork's `-file <map>` (menu bypass) and `-buildmapcache`. `-map`,
  `-noaudio`, `-nomusic` and `-novideo` are debug-only upstream. `-headless`
  skips all GUI/WND/SDL/GPU work.
- **`-file` wants the short map form** (`Maps/WPTest.map`): the command-line
  parser always expands it to `Maps\WPTest\WPTest.map`. Passing the long form
  doubles the directory and loads an *empty world* (`extentW=0`, no sides, the
  local player becomes a neutral observer). The in-engine shell's map start
  wants the long form.
- **`WP_BOOT_MAP`** boots straight into a map through the same path as
  `-file` but without `m_initialFile`, so match end returns to the in-engine
  shell instead of quitting. It is a native run switch, like `WP_DIFFICULTY`;
  nothing in the browser shell sets it — browser deploys go through the
  in-engine shell and the `_wpShowMission` export.

## Zero-default landmines

Fields the retail INI always sets, so the code never defends their absence.
Each of these produced a silent failure before the dataset authored it.

| Field (block) | Default without it | Symptom |
|---|---|---|
| `Object DefaultThingTemplate` | every template's `m_assetScale` stays 0 | every model at scale 0: invisible, no error |
| `PartitionCellSize` (GameData) | 0 | shroud division by zero |
| `CameraPitch` / `CameraHeight` (GameData) | 0 | camera stares at the horizon |
| `MaxLineBuildObjects` (GameData) | 0 | zero-length placement-icon array; every placement leaks its translucent preview under the real building, which appears as a "ghost" when the building dies |
| `Gravity` (GameData) | `-1.0` raw, i.e. per-frame² (~9× stock) | no `Lift` can win; hover aircraft drive on the ground. Author `Gravity = -100` |
| `TerrainLOD` (GameData) | `AUTOMATIC` | the first-frame LOD benchmark leaves `drawTerrainOnly` set on this port: no shadows, no particles. Pin `TerrainLOD = MAX` |
| `DragTolerance` / `DragToleranceMS` / `DragTolerance3D` (Mouse.ini) | 0 | every click is a "drag": right-click never cancels placement |
| `GuardInnerModifier` / `GuardOuterModifier` etc. (AIData.ini) | 0 | acquire range 0 engine-wide: nothing ever auto-targets |
| `AudioSettings` (full block) | zeroed sample counts and volumes | silent audio |
| `MaxParticleCount` via LOD presets | 0 | particles capped at zero (`ALWAYS_RENDER` priority is exempt) |
| `WaterSet <TOD>` ×4, `WaterTransparency`, `Weather` singletons | null `OVERRIDE<T>` globals | later dereference |
| `MinTurnSpeed` (wheeled Locomotor) | `BIGNUM` | `Appearance = FOUR_WHEELS` scales steering by `actualSpeed / MinTurnSpeed`: vehicles drive straight past goals however high `TurnRate` is |
| `AllowAirborneMotiveForce` / `Apply2DFrictionWhenAirborne` (flying Locomotor) | No | airborne units ignore move orders, or skate in orbits |
| KindOf `SCORE` (units also `INFANTRY`/`VEHICLE`) | absent | every ScoreKeeper counter stays 0 |

Unknown INI blocks and fields die through a compiled-out `DEBUG_CRASH` in
release; this fork prints `FATAL INI: … Unknown block/field` and
`FATAL INI: error parsing block …` to stderr before the crash macro. An
`AudioEvent` with an unknown field still segfaults inside its table walk (the
valid range fields are `MinRange`/`MaxRange`).

## Hard-coded names the engine looks up

| Name | Where | Consequence when missing |
|---|---|---|
| `EXScorch01.tga` | terrain scorch atlas (4×4 UV grid, three marks per row) | no scorches; ours is generated by `tools/gentex.py` |
| `Locater01` / `Locater02` | placement-cursor models | `W3DFS_MISS` spam, invisible placement cursor |
| `RallyPointMarker` (ThingTemplate) and KindOf `AUTO_RALLYPOINT` | `ControlBar::showRallyPoint` | rally points cannot be set |
| `BasicHumanLocomotor` | rally-point path probe | every rally attempt fails as "no path" |
| `GUIClick`, `GUIClickDisabled`, `NoCanDoSound` (AudioEvents) | UI feedback | silent denials |
| `GUI:CantBuild*`, `GUI:RallyPointSet`, `GUI:RallyPointNoPath`, `DOZER:ConstructionComplete`, `CONTROLBAR:UnderConstructionDesc` … | string table | raw labels |
| `PowerPointG` / `PowerPointY` / `PowerPointR` / `PowerBarSlider` (MappedImages) | `W3DPowerDraw` | the power meter returns without drawing |
| `ButtonCommand01..18`, `ButtonQueue01..09`, `MoneyDisplay`, `PowerWindow` (ControlBar.wnd) | `ControlBar` | queue buttons are dereferenced unguarded; missing money/power windows once made `InGameUI::update` bail before the whole context-sensitive UI ran |
| `Command_CancelUnitCreate` / `Command_CancelUpgradeCreate` (CommandButtons) | build-queue tiles | no cancel/refund |
| The rally-line model and texture (retail `SCMNode` / `EXLaser.tga`) | `W3DWaypointBuffer` | no rally line; no longer hard-coded — `RallyPointModel` / `RallyPointLineTexture` in `GameData.ini` (table below), and this fork null-guards the six dereferences |
| `TBBib`, `TBRedBib`, `TSCloudMed`, `TSNoiseUrb`, `exlaser`, `exmask_g`, `noise0000`, `tsmoonlarg`, `twalphaedge`, `twwater01`, `watersurfacebubbles`, `shadow.tga` | terrain, water, cloud, effect and decal shaders | magenta placeholders; the dataset ships solid-colour originals under these names |
| The 56 `WindowTransitions.ini` names | shell transitions | `remove()` on an unknown name null-derefs (patched) |

Placeholder sharing is a build failure by policy: `tools/lint_voices.py` fails
staging when two templates share a voice event, an event is missing from
`SoundEffects.ini` or a WAV is missing on disk.

## Fork switches in `GameData.ini`

Behaviour this fork once hard-coded is read from the `GameData` block by
`GlobalData.cpp`. Every default is the retail behaviour, so an unmodified
dataset is unaffected; `data/Data/INI/GameData.ini` sets the War Powers
values.

| Field | Default (retail) | War Powers | Effect |
|---|---|---|---|
| `RallyPointModel` | `SCMNode` | `WPNODE01` | Rally-point node model drawn by `W3DWaypointBuffer` |
| `RallyPointLineTexture` | `EXLaser.tga` | `wp_rallyline.tga` | Rally-line texture |
| `DozerResumesAbandonedConstruction` | `No` | `Yes` | Idle dozers resume nearby abandoned own construction sites from the "bored" check |
| `MapPlacedHarvestersAutoGather` | `No` | `Yes` | Map-placed haulers enter their harvesting state at match start; restored saves keep their orders |
| `CommandButtonAvailabilityCues` | `No` | `Yes` | Padlock badge and brightened portraits on command buttons (D024) |
| `MusicRotation` | empty | `Track_WP_01` … `Track_WP_06` | Ordered background-music rotation of `Music.ini` events, played by `GameEngine::update`; an empty list leaves the stock music handling alone |

## Format contracts

### Maps and scripts

- **Win/lose conditions in single-player are map scripts** (`VictoryConditions`
  proper is multiplayer-gated). The `PlayerScriptsList` chunk must be **nested
  inside `SidesList`** — the reader only registers it there; the top-level
  registration is for `.scb` files. `ScriptList` sub-chunk order maps 1:1 to
  side order.
- Chunk versions from the `Scripts.cpp` writers: Script v2 (name + three
  comment strings + six flag bytes + `delayEvaluationSeconds`) containing
  OrCondition v1 (nested Condition v4) and ScriptAction v2. **v4/v2 condition
  and action chunks carry the internal-name key and the engine rematches the
  type by name** — write ordinal 0 plus the name (`NAMED_DESTROYED`,
  `VICTORY`, `DEFEAT`, …). Parameter type ordinals *are* positional
  (`UNIT` = 14, `OBJECT_TYPE` = 15, `ATTACK_PRIORITY_SET` = 28); parameters
  serialize as int type + int + float + string (`COORD3D` excepted).
- A script's three difficulty flag bytes select which difficulties run it:
  `ScriptEngine::setGlobalDifficulty` comes from `MSG_NEW_GAME`, and this is
  how per-difficulty AI escalation timers are authored.
- Map objects get script names through the `objectName` dictionary key;
  `NAMED_DESTROYED` stays true after full removal. `VICTORY` = input off +
  120-frame banner + `exitGame`; in `-file` mode the engine quits to desktop
  after the banner, in menu/`WP_BOOT_MAP` mode it returns to the shell.
- **Build-list wire format** (SidesList v3, per side): buildingName,
  templateName, x, y, z (→ 0), angle, byte initiallyBuilt, int numRebuilds,
  script, int health, bytes whiner/unsellable/repairable. The team count in
  the sides chunk must be derived from the collected team dictionaries — an
  under-declared count makes the reader consume a trailing team as garbage
  and the map loads with **zero objects** (no error, black shroud).
- Every map-placed object with a Draw module needs a Body module, scenery
  included: `Drawable::onLevelStart` asks the body for its damage state while
  preparing ambient sound. `tools/check_content.py` enforces this.
- A looping `Limit = 1` ambient (`WP_AMB_Wind`) tolerates exactly one carrier:
  `Drawable::updateDrawable` re-requests a non-playing looping ambient every
  frame, so a second carrier is rejected by `GameSounds` ~30×/s for the whole
  match. `tools/genmap.py` places one neutral, invisible `WP_AmbientWind`
  emitter at the playable centre; `tools/validate_gameplay.py` enforces both.
- `tools/genmap.py` writes all of the above; `tools/validate_gameplay.py`
  decodes the binaries independently.

### W3D models and animation

- `tools/genw3d.py` writes engine-valid meshes from the byte spec of the GPL
  reader; W3D names are ≤ 15 characters (`W3D_NAME_LEN` = 16) and name keys
  are case-insensitive. `W3DDefaultDraw` is a no-op in release builds
  (constructor body under `LOAD_TEST_ASSETS`): INI objects must use
  `W3DModelDraw` with `DefaultConditionState / Model = … / End`.
- **Skeletal animation** (`tools/genrig.py`): HIERARCHY (pivot quaternion +
  translation base pose), ANIMATION (delta channels composed onto the base
  pose, translate-then-post-multiply), bone-bound HLODs whose sub-object
  vertices are in bone-local coordinates. The registered animation name is
  `HIER.ANIM` and load-on-demand derives the *filename* from the part after
  the dot (`WPINF1.WPINF1WLK` loads `wpinf1wlk.w3d`); the hierarchy lives in
  its own `wpinf1.w3d`. INI: `Animation = WPINF1.WPINF1WLK 5.4` (distance
  syncs walk rate); `IdleAnimation` must pair with `AnimationMode = ONCE`
  (LOOP throws in release, silently without the FATAL INI print).
- Named `TURRET` pivots with turret-relative `MUZZLE` attachments, `CARGO`
  meshes for haulers, `HOUSECOLOR` regions for ownership, and `W3DTruckDraw`
  wheel bones are the production contracts recorded in
  [art-pipeline.md](art-pipeline.md).
- Blender export (`OpenSAGE.BlenderPlugin`): `bpy.ops.export_mesh.westwood_w3d(
  filepath, file_format='W3D', export_mode='HM', force_vertex_materials=True)`.
  The container name comes from the filename, the mesh name from the Blender
  mesh datablock, the texture stage and UVs from a Principled BSDF image node.
  Imported material datablocks bake **black** in headless Cycles: replace them
  with fresh `bpy.data.materials.new()` datablocks before baking. Strip vertex
  groups from imported rigs or the exporter treats the mesh as skinned.
- `WP_FRAME_DUMP` TGAs are **top-down** (descriptor bit 0x20); decode
  accordingly or the UI looks upside-down. `tools/tgadiff.py` handles it.

### INI syntax notes

- `ParticleSystem.ini` keyframes: `Color1 = R:x G:y B:z frame`,
  `Alpha1 = lo hi frame`; enum lists in `ParticleSys.h`. `FXList.ini` nuggets
  (`ParticleSystem`, `ViewShake`, `TerrainScorch`, `Sound`). Templates load in
  `ParticleSystemManager::init`, before FXListStore and WeaponStore.
- `ProjectileDetonationFX` never fires on projectile-less weapons; a weapon
  needs a `ProjectileObject` with `DumbProjectileBehavior` (bezier
  `FirstHeight`/`SecondHeight`/`PercentIndent`, `DetonateCallsKill = Yes`) for
  impact effects and exactly-once damage at detonation. Projectiles outlive
  their shooter.
- The 2D icon chain is Animation block → MappedImage → TGA. The block keyword
  in `Animation2D.ini` is **`Animation`**, not `Animation2D`; `MappedImage`
  `Status = NONE` is invalid.
- `Control = loop` + `LoopCount = 0` is a permanent loop; `Control = INTERRUPT`
  lets a new voice preempt a playing one. `Command = NONE` is a valid
  no-op CommandButton. `MinimumAttackRange` plus `ScatterRadius` gives
  artillery its dead zone.
- Hover aircraft recipe: `Surfaces = AIR`, `Lift`, `PreferredHeight` (+
  damping), `SpeedLimitZ`, `ZAxisBehavior = SURFACE_RELATIVE_HEIGHT`,
  `Appearance = HOVER`, `AllowAirborneMotiveForce = Yes`,
  `Extra2DFriction = 2.0`, `Apply2DFrictionWhenAirborne = Yes`. Airfield-based
  jets need `JetAIUpdate` and parking data; hover craft do not.
- `UnicodeString::format` reads `%d` against a `Real` as garbage; string-table
  format specifiers must match the argument types at the call site, and wide
  strings use `%ls` on POSIX.

### WND layouts

- Layout-block callbacks are **unquoted** (`LAYOUTINIT = WPMainMenuInit;`);
  window-level `SYSTEMCALLBACK = "…"` stays quoted. A quoted layout callback
  resolves to null silently.
- A pushed layout **must** declare `LAYOUTSHUTDOWN` that calls
  `TheShell->shutdownComplete()`, or push/pop waits forever.
- `W3DGameWinDefaultDraw` draws colour fills only when `WIN_STATUS_IMAGE` is
  absent; a DRAW callback replaces the default background/border paint
  entirely. Sibling windows z-fight in declaration order and both draw; the
  *later* sibling wins the input hit-test even if the earlier one is drawn.
- An empty `TEXT = "";` is a native crash (`strlen(NULL)`); omit the field for
  runtime-filled labels. `TEXT = "WP:Label"` resolves through the string table.
- A gadget's `GBM_SELECTED` goes to its *owner*; buttons and containers need
  `SYSTEMCALLBACK = "PassSelectedButtonsToParentSystem"` to bubble to the
  ControlBar's `ControlBarSystem` callback. `GadgetButtonSetText` is dropped by
  that pass-through — use `winSetText` directly.
- A click whose whole hit chain returns `MSG_IGNORED` is treated as unused and
  falls through to the world (a disabled build button became a rally order).
  `WPHudSwallowInput` on the bar's parent consumes those, except an UP whose
  DOWN happened in the world.
- Build-queue tiles draw the ThingTemplate `ButtonImage`, not the
  CommandButton's; a tooltip's third row is the CommandButton `DescriptLabel`.
- `tools/genwnd.py` generates every layout, including the 48-window
  ControlBar, `ControlBarPopupDescription.wnd` and the result screens.

## Gameplay systems

- **Construction is dozer-built** (D016): `DozerAIUpdate`, `MSG_DOZER_CONSTRUCT`
  (template id, location, angle; the selected group is the dozer), the
  placement UI and construction-percent rendering are stock paths. Any player
  command to a dozer cancels its current task and placing a second building
  cancels the pending first; with `DozerResumesAbandonedConstruction = Yes`
  (a `GameData.ini` switch, retail default `No`) idle dozers resume abandoned
  own sites from the "bored" check, and this fork recomputes the build
  approach point from *current* positions each time (the stock precomputed
  dock point could sit inside the footprint and wedge the dozer forever).
  `WP_AUTOTEST=wedge` is the gate.
- **Fog:** `ShroudOn = Yes` runs the full partition shroud. The object shroud
  pass (`ShroudTextureShader`, camera-space texgen) no-ops through d8web, so
  this fork skips rendering `OBJECTSHROUD_SHROUDED` objects and renders
  `OBJECTSHROUD_FOGGED` ones with the fogged light environment. Own objects
  are always `CLEAR` (never snapshotted, always labelled); under-construction
  sites are excluded from fog-memory ghosts. Shroud/ghost transitions only
  evaluate for drawn objects.
- **Placement previews** auto-cancel when the source dozer dies, and any
  preview drawable that outlives placement mode is destroyed next frame.
- **The plain `AIPlayer`** (not `AISkirmishPlayer`/`.scb`) is the opponent:
  its constructor turns unit production *off* (campaign convention), so the
  side's scripts must run `PLAYER_ENABLE_UNIT_CONSTRUCTION`; team production
  conditions are named scripts; `findFactory` searches the build list only
  (pre-placed factories are registered by `AIPlayer::newMap`);
  `isPossibleToMakeUnit` needs the unit in the producer's command set;
  `Team::tryToRecruit` poaches from lower-priority teams within
  `MaxRecruitRadius` and treats the default team as always poachable, so map
  garrisons need their own high-priority, non-recruitable team.
  `PLAYER_DESTROYED_N_BUILDINGS_PLAYER` was a stub upstream and is implemented
  here through `ScoreKeeper::getTotalBuildingsDestroyedOfPlayer`; kills of
  under-construction buildings do not count.
- **Match results** reach the shell through `WPRecordMatchResult` at
  `VICTORY`/`DEFEAT` time (player data is gone by teardown) and the browser
  through `Module.onMatchResult`; `GameLogic::quit(FALSE)` with no quit menu
  open only *opens* the menu, so headless harnesses quit twice.
- **Music rotation** is this fork's: `GameEngine::update` polls
  `TheAudio->isCurrentlyPlaying` and starts the next track from the
  `MusicRotation` list in `GameData.ini` (empty by default, so a retail
  dataset keeps its own music handling).
- **Idle dozers** re-assert registration every idle tick; the stock flag
  orphaned any dozer that went idle during map load.

## Shell, transitions and the browser page

- The in-engine shell (`WPShell.cpp`) is the only menu; the page is a loader
  and, in a match, a HUD overlay driven by `Module.onGameState` snapshots
  (see [web-bridge.md](web-bridge.md)). Stock EA menu code stays dormant.
- `Intro::doPostIntro` runs every frame once the intro is done; its
  `m_breakTheMovie` render freeze is armed one-shot on this fork or any shell
  screen re-freezes the scene. `GameLogic::startNewGame` pops shell screens
  and clears the flag so `-file`/`WP_BOOT_MAP` matches render and pick.
- Transition styles dereferenced their window unguarded mid-play; destroying
  a menu during a fade wrote low memory every frame in WASM (a silent black
  second match) and segfaulted natively. All entry points null-guard.
- `g_wpMenuCurtain` paints a black fill before `End_Render` from the quit
  confirmation or `clearGameData` until the next shell or match paints, which
  removes the raw-world flicker between matches. The dead match world keeps
  rendering behind the shell; an opaque backdrop child hides it.
- `Options.ini` is written by the page before startup, so gameplay and
  rendering settings need a restart; channel audio and overlay appearance
  apply immediately. HTML panels acquire and release only their own pause
  through `wpSetWebPause`; native Escape/P pauses survive closing a panel.
- Checkpoints: a native save writes `Save/wp-checkpoint.sav` under the IDBFS
  user directory with a sidecar for compatibility and mission identity; native
  portable map paths are lowercased in saves, so the bridge canonicalizes
  known map IDs after load. Serialize save requests across panel reopenings.
- Large scalar `EM_ASM` calls can compile yet fail when a referenced `$16` is
  absent from the generated signature; the state snapshot is one contiguous
  numeric buffer plus string pointers, copied synchronously in the callback.
- Hidden tabs suspend `requestAnimationFrame`, so logic, audio and the boot
  fade all freeze; the product treats it as auto-pause.

## Browser audio (miniaudio under Emscripten)

Two stacked bugs made every sound silent while the device pulled fine:

1. The non-FFmpeg decode path built `ma_audio_buffer`s from a config whose
   channel count `ma_decode_memory` never writes back — **0 channels**, so the
   cursor pinned at 0 forever. Request a concrete output format
   (`s16`, 2 channels, 44100 Hz); miniaudio converts.
2. Sound groups never enter the node graph on this build; attach sounds
   directly to the engine endpoint under `__EMSCRIPTEN__`.

The `[AUDIO*]` traces that found them are `IG_TRACE`-gated and permanent. The
trace gate statics latch at first call, so device-open traces need the flag set
before `main()` (the page's `preRun`).

## Native development (macOS)

- Configure with `cmake --preset macos-vulkan -DSAGE_DXVK_USE_LOCAL_FORK=ON`
  (see the engine README); the build needs `VCPKG_ROOT` and the LunarG SDK's
  `setup-env.sh` sourced. `RTS_DEBUG_CRASHING=ON` does not compile on macOS.
- Launch through `run.sh` (it composes the Vulkan ICD and `DYLD_*` variables);
  a bare binary dies with a misleading Vulkan/D3D error, and SIP strips
  `DYLD_*` when exec'ing protected binaries such as `/bin/bash` or `perl`.
  A test launch needs `-file Maps/WPTest.map` or the engine idles at the shell.
- **Never `cp` over a previously executed binary:** same-inode replacement
  trips the kernel signature cache → instant SIGKILL (exit 137, no output).
  `rm`, `cp`, then `codesign -s - -f`.
- stdout is block-buffered through pipes (harness prints go to stderr);
  piping builds through `tail` masks exit codes; RelWithDebInfo crash-report
  line attribution is unreliable, so breadcrumbs beat forensics.
- Presenting blocks forever while the window is occluded (locked screen): use
  `WP_PRESENT_SKIP` for unattended runs. A process stuck there survives
  `SIGTERM`; `pkill -9` and check `pgrep` before the next run. Never create a
  Metal device inside a dyld initializer.

### DXVK fork fixes (native renderer, `engine/references/fbraz3-dxvk`)

1. Dummy vertex binding bound with length 0 → out-of-bounds null-attribute
   fetches; now binds the dummy's full length.
2. Dummy vertex binding stride 0 → Metal silently kills the draw (far terrain
   rows missing); now stride 16.
3. Spec-constant UBO never created without `VK_EXT_graphics_pipeline_library`
   (which MoltenVK lacks) → null `spec_state` in every argument buffer; now
   always created on Apple platforms.

## Player-experience integration contracts

- Native map scripts decide objectives and results; the page's telemetry is
  observational. `WP_AUTOTEST=mission` changes explicit prerequisites, target
  survival or timer expiry and observes native counters and results; it never
  dispatches a victory action itself. The expected-result latch is separate
  from `inGame`, which stays true during the end-game banner. Diagnostic
  sessions never persist forced results into a player's operation record.
- Native test fixtures must complete the normal Create-module lifecycle:
  `SupplyCenterCreate::onBuildComplete` registers a depot with the resource
  manager, so a merely allocated depot lets trucks collect but never deliver.
  Identify produced trucks by producer ID (skirmish maps also have starting
  haulers). With `MapPlacedHarvestersAutoGather = Yes` (`GameData.ini`; retail
  default `No`) map-placed haulers are put into their harvesting state on a
  fresh start; restored saves keep their orders.
- Wheel locomotors use 15 world units/second `MinTurnSpeed` for scouts, 6 for
  heavy artillery, 10 for Porters and 12 for Scavengers, with
  `CanMoveBackwards = Yes`; `tools/validate_gameplay.py` rejects missing or
  unattainable turn speeds. Economy fixtures are delivery regression checks
  (starting haulers are included), not throughput or balance measurements.
- `WP_REVIEW_SCENE=1` builds a bounded roster review on the Flats;
  `stress` adds a bounded mixed-army encounter. Both bypass production and are
  separate from input-driven tests, normal matches and balance evidence.

## Debugging methodology (lessons that cost days)

- When a *state bit* is wrong, first verify that the *writer of that bit runs
  at all* (the invisible-unit saga: `Visibility_Check` never executed because
  the render freeze was never cleared).
- Never trust budget-capped logging to characterize steady state; run an
  unbudgeted long-horizon counter first, and before instrumenting a draw
  pipeline confirm the camera is looking at the object *in the failing
  frames* (edge-scroll had marched the camera off the base within two
  seconds of every unattended run).
- When a scripted end condition fires "impossibly", trace the object's death
  first (the phantom 45-second defeat was a real kill by a poached garrison).
- `StateMachine::getCurrentStateName()` is stubbed to empty in release — use
  `getCurrentStateID()`. The corner `50(50)` readout is the FPS counter; the
  logic frame is `TheGameLogic->m_frame`.
- In the browser, the console rotates: grep the page's DOM log for ground
  truth, and drive verification through short `MainLoop.func()` pump bursts
  while a tab is throttled. A "frozen" engine in a hidden tab is the browser
  suspending `rAF`.
- Placeholder cross-wiring must trip a lint or a logged TODO; silent reuse
  reads as shipped content.

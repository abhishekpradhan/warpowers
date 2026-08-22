# Engine Notes — GeneralsX/ZH boot requirements (for the zero-retail dataset)

Condensed from a full source exploration + empirical bring-up, 2026-08-21. The Zero Hour build is the `GeneralsMD/` tree (`z_generals` target → `GeneralsXZH`); shared code in `Core/`; `GeneralsZH/` holds only GeneralsX's replacement `ExtrasMenu.wnd`.

## The three-bucket shape of the minimal dataset

1. **~46 must-exist INI paths** — the engine hard-dies (`throw INI_CANT_OPEN_FILE` → `RELEASE_CRASH`) on any missing one, but shrugs at dangling references inside them (all cross-reference validators are no-op in release). Each `Data\INI\X` demand is satisfied by `Data/INI/X.ini` *or* any `.ini` inside `Data/INI/X/`. Full list lives in our authored dataset (`data/Data/INI/**`).
2. **Exactly one must-exist binary asset:** ≥1 music file — `GameEngine.cpp:622` silently sets quitting if no `MusicTrack`'s resolved file exists on disk. Path = `AudioSettings.AudioRoot\MusicFolder\Filename`. (Ours: `wp_ambient_01.mp3`.)
3. **A handful of must-exist WND layouts** whose absence causes null-deref segfaults, not clean errors: `Menus/MainMenu.wnd`, `Menus/BlankWindow.wnd`, `ControlBar.wnd` (+ every named child the code references — we generate all 117), `GeneralsExpPoints.wnd`, `ControlBarPopupDescription.wnd`, `ReplayControl.wnd`. Missing WND *file* → `winCreateFromScript` returns null harmlessly; missing named *window* → crash at the unguarded lookups.

Everything visual degrades gracefully: missing W3D model → invisible object; missing texture → magenta placeholder; missing shader → logged error; missing CSF strings → raw labels.

## Key mechanics

- **Loose files beat archives; archives are optional.** `StdBIGFileSystem` mounts every `*.big` (no hardcoded names) but boots happily with zero. Ship everything loose.
- **Asset root resolution** (in order): `$CNC_GENERALS_ZH_PATH` → `$GENERALSX_ASSET_PATH` → `$CNC_ZH_INSTALLPATH` → `Options.ini [Paths]` → registry.ini → `<exedir>/../Resources` → `<exedir>` → CWD. run.sh cd's to the game dir, so CWD wins.
- **User data dir** (saves, maps, registry.ini): `~/Library/Application Support/GeneralsX/GeneralsZH/`. User maps ARE disk-scanned; asset-root `Maps/` needs `MapCache.ini` unless `-buildmapcache` (which we patched into release).
- **Singleton INI blocks** must exist or `OVERRIDE<T>` globals stay null and later deref: `WaterSet <TOD>` ×4 + `WaterTransparency` (Water.ini), `Weather` (Weather.ini). Same pattern likely for others as we go deeper.
- **`Object DefaultThingTemplate` is load-bearing** (ThingFactory.cpp:137): every new object template copies its baseline from a template literally named `DefaultThingTemplate`. The ThingTemplate ctor never initializes `m_assetScale`, so without this template every model is created at **scale 0** (vertices collapse to −0.0 — invisible, no error). Ours sets `Scale = 1.0`; retail's sets many more baselines — expect more zero-default finds seeded here.
- **`W3DDefaultDraw` is a no-op in release builds** (constructor body is `#ifdef LOAD_TEST_ASSETS`); INI-declared objects must use `W3DModelDraw` with `DefaultConditionState / Model = <name> / End`.
- **GameData zero-defaults found so far** that retail INI normally sets: `PartitionCellSize` (0 → shroud div-by-zero), `CameraPitch/CameraHeight` (0 → horizon-staring camera). `ShroudOn = No` is a valid data toggle.
- **W3D models**: `tools/genw3d.py` generates engine-valid meshes (byte spec from the GPL reader; see the tool). **RESOLVED 2026-08-22 — the "invisible mesh bug" was never a rendering bug.** Meshes rendered correctly all along; in every unattended run the mouse cursor sat at screen corner (0,0), the RTS **edge-scroll** marched the camera off the base within ~2s of match start, and the meshes were then *correctly* frustum-culled. They did render during the first frames — under the fade-from-black — which is exactly the window all budget-capped instrumentation sampled, manufacturing days of false "draws submit, no pixels" evidence. Fix for the headless dev loop: `HorizontalScrollSpeedFactor = 0.0` / `VerticalScrollSpeedFactor = 0.0` in GameData (restore for real input work). Two secondary data findings: `UseBehindBuildingMarker = No` (with it on, structures are routed to the stencil-occlusion flush path, unverified on this port), and maps must be big enough for the camera-area constraints at CameraHeight (a 640×640-world map collapses the constraint box; WPTest is now 160×160 cells = 1600×1600). **Lessons burned in:** (1) never trust budget-capped logging to characterize steady-state behavior — always run an unbudgeted long-horizon counter first; (2) before instrumenting a draw pipeline, verify the camera is looking at the object *in the failing frames*, not in frame 1. The GPU-forensics detour still paid: three real latent bugs found and fixed in the DXVK fork (see below), plus a validated Metal/Vulkan instrumentation toolkit (`WP_DXVK_SPY` in the fork; MoltenVK-source spies in `~/MoltenVK-src`, not shipped).
- **Transition groups:** every name in code must exist in `WindowTransitions.ini` (56 names, predefined) — engine bug: `remove()` on unknown name null-derefs via `null == null` (patched in our branch).
- **Flags in release build:** `-win -fullscreen -headless -xres -yres -noshellmap -noShellAnim -nologo -quickstart -mod -noshaders`, plus our patch adds `-file <map>` (menu bypass) and `-buildmapcache`. `-map/-noaudio/-nomusic/-novideo` remain debug-only upstream. **`-headless` skips ALL GUI/WND/SDL/Vulkan — the future CI harness.**
- **Language:** resolves to `english` via the port's registry.ini default; `Data/english/` holds Language, HeaderTemplate, CommandMap.

## macOS build gotchas (hard-won)

- Build needs `VCPKG_ROOT` and the LunarG SDK env: `source ~/VulkanSDK/1.4.357.1/setup-env.sh` (the build script checks the SDK but doesn't export `VULKAN_SDK` — upstreamable fix).
- `RTS_DEBUG_CRASHING=ON` does not compile on macOS (MSVC `__int64` in Debug.h profile structs).
- **Never `cp` over a previously-executed binary** — same-inode replacement trips the kernel's signature cache → instant SIGKILL (exit 137, zero output). `rm` first (deploy script needs this fix).
- Piping build commands through `tail` masks their exit codes. Don't.
- Crash-report line attribution in RelWithDebInfo is unreliable (a "ThingFactory::reset" stack was actually a different site); `fprintf` breadcrumbs + rebuild beat forensics.
- **DYLD_INSERT_LIBRARIES is stripped when exec'ing SIP-protected binaries** (i.e. `/bin/bash`, so any env you set before `run.sh` is gone by the time the game launches). Compose the full env inline and exec `./GeneralsXZH` directly, the way our test harness does.
- **Never touch Metal (create a device/encoder) inside a dyld initializer** — the AGX driver's lazy internal-shader compile aborts the process (SIGABRT in `getRangeExecutionVariant`). Defer to a dispatch_after.
- **Present blocks forever when the window is occluded** (locked screen): CAMetalLayer starves drawables → DXVK `Presenter::acquireNextImage` waits on a condvar indefinitely. Use `WP_PRESENT_SKIP=100000000` (engine feature) for headless runs; `WP_FRAME_DUMP` still captures real frames. Also: a game stuck there survives `pkill` (TERM) — a zombie instance then poisons later runs; use `pkill -9` and check `pgrep` before every run.
- The engine's own shutdown crashes in `TerrainTracksRenderObjClassSystem::shutdown()` on SIGTERM (pre-existing destructor bug, harmless noise in crash reports).
- ObjC-swizzle spies cannot see MoltenVK's encoder calls usefully (dispatch goes through per-frame recreated encoders + selector stubs; our hooks verified installed yet never fired for reasons ultimately mooted by the real root cause). The productive instrumentation layers are: DXVK source (we own it), MoltenVK source (built from `~/MoltenVK-src`, `make macos` with `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`), and engine breadcrumbs.

## DXVK fork fixes found during the hunt (all committed on `warpowers-dxvk`)

1. **Dummy vertex binding bound with length 0** → every null-attribute fetch was out-of-bounds, undefined without robustness2 (the exact configuration the fallback exists for). Now binds the dummy's full length.
2. **Dummy vertex binding stride 0** → with dynamic strides, Metal gets `attributeStride:0` on a per-vertex layout and the AGX driver silently kills the draw. Visible symptom: far-terrain rows missing (their fix restored them). Now stride 16.
3. **Spec-constant UBO never created without `VK_EXT_graphics_pipeline_library`** (which MoltenVK lacks; our patchset waives DXVK's requirement) → every shader's `spec_state` pointer in the Metal argument buffer was NULL, a latent GPU null-deref for any pipeline variant that reads it. Now always created/bound on `__APPLE__`.

## State as of 2026-08-22

**The first match renders: terrain + a visible command center model, 100% original data, fully headless with the screen locked.** Boot-Slice step 2 (visible models) complete: `WP_PRESENT_SKIP=100000000 WP_FRAME_DUMP=/tmp/f.tga ./GeneralsXZH -win -noshellmap -file Maps/WPTest.map` yields a frame with the WPCC01 box centered at the player's base. Remaining Boot-Slice: input (select / build tank / move / attack — will need scroll factors restored + real mouse), win condition. Carried-over guard: `InGameUI::update` money/power HUD bail (window lifecycle across end-of-init reset still to be understood).

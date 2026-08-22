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
- **W3D models**: `tools/genw3d.py` generates engine-valid meshes (byte spec from the GPL reader; see the tool). Verified loading through: prototype registration → scene add → frustum → DX8 batch registration → draw-task submission. **Open issue — mesh draws produce no pixels (macOS port).** Systematically eliminated with instrumentation (traces on engine branch `bfe77cfb`): depth (forced ZFUNC ALWAYS), stencil, alpha test/blend, colorwrite, fog, FF lighting, draw order (meshes draw seq 37–39 of 46, after terrain), overdraw erasers (skipping late draws changes nothing), view/projection/world matrices (identical to terrain's at draw time; world correctly (160,160,10)), VB contents (correct vertices verified in-buffer), forced VB/IB rebinding. `DrawIndexedPrimitive` submits with correct params every frame. **Conclusion: the failure is below the engine, in the GeneralsX DXVK fork's d3d8 layer.** External research (session 2026-08-21): the fork is frozen at DXVK 2.6 + a hand-rolled macOS patchset that disables robustness2/nullDescriptor and substitutes a silent zero dummy buffer for null vertex bindings, and hand-edits the d3d8 UP-draw batcher ("null D3D9 backing") — a bespoke path with exactly this failure signature; upstream merged a year of d3d8 correctness fixes the fork lacks (DISCARD semantics #5155, ZBIAS #5312/#5431). **Next levers (fresh session): (1) full Xcode Metal GPU frame capture (decisive: shows whether the draw reaches the encoder and with what vertex data); (2) rebase the DXVK fork onto current upstream + reapply the ~149-line patchset (the fix vehicle regardless); (3) file our minimal zero-retail repro upstream to fbraz3/GeneralsX — likely helps their open #240 too.** Note: one earlier "sky box visible" result is suspect (rendered white despite red emissive — possibly a water quad, not our mesh).
- **Transition groups:** every name in code must exist in `WindowTransitions.ini` (56 names, predefined) — engine bug: `remove()` on unknown name null-derefs via `null == null` (patched in our branch).
- **Flags in release build:** `-win -fullscreen -headless -xres -yres -noshellmap -noShellAnim -nologo -quickstart -mod -noshaders`, plus our patch adds `-file <map>` (menu bypass) and `-buildmapcache`. `-map/-noaudio/-nomusic/-novideo` remain debug-only upstream. **`-headless` skips ALL GUI/WND/SDL/Vulkan — the future CI harness.**
- **Language:** resolves to `english` via the port's registry.ini default; `Data/english/` holds Language, HeaderTemplate, CommandMap.

## macOS build gotchas (hard-won)

- Build needs `VCPKG_ROOT` and the LunarG SDK env: `source ~/VulkanSDK/1.4.357.1/setup-env.sh` (the build script checks the SDK but doesn't export `VULKAN_SDK` — upstreamable fix).
- `RTS_DEBUG_CRASHING=ON` does not compile on macOS (MSVC `__int64` in Debug.h profile structs).
- **Never `cp` over a previously-executed binary** — same-inode replacement trips the kernel's signature cache → instant SIGKILL (exit 137, zero output). `rm` first (deploy script needs this fix).
- Piping build commands through `tail` masks their exit codes. Don't.
- Crash-report line attribution in RelWithDebInfo is unreliable (a "ThingFactory::reset" stack was actually a different site); `fprintf` breadcrumbs + rebuild beat forensics.

## State as of 2026-08-21

**The engine runs indefinitely on 100% original data** (main loop, window manager live, ~45s+ verified, zero EA bytes). Current debug guard: `InGameUI::update` bails when money/power HUD windows are absent at the shell (they exist at init, are missing at update — window lifecycle across the end-of-init reset still to be understood). Next: `-file` straight into a minimal authored map with a real object roster.

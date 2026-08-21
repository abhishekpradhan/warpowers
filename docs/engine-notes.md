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

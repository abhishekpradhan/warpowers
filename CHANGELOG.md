# Changelog

All notable changes to War Powers are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Nothing yet.

## [0.1.4] - 2026-09-26

Feedback batch from the first public playtests.

### Added

- Keyboard orders: `A` enters attack-move targeting and `G` guard targeting
  (new bindable `TOGGLE_ATTACKMOVE` and `GUARD` commands; guard presses the
  button named by the new `GuardCommandButton` GameData switch). Both are
  remappable in Settings.
- Build and train hotkeys: every command button carries a letter (`&` in its
  label), shown highlighted in the tooltip while the builder or factory is
  selected; the tooltip name text uses `HOTKEY_TEXT`. `C` on a construction
  site cancels it.
- Shift queues movement orders as waypoints and adds units to the selection
  (`PreferSelectionQueuesWaypoints` GameData switch; the prefer-selection
  modifier was not bound before).
- Camera bookmarks: Ctrl + F5–F8 save a view, F5–F8 recall it.
- Screen-edge scrolling in the browser, driven by the page (the engine only
  edge-scrolls with a captured cursor): the pointer in the edge band of the
  battlefield or beyond it, on the black frame, holds the arrow keys down;
  a HUD control, an open panel, a hidden tab or lost focus release them.
  Settings toggle, on by default.
- Optional WASD camera keys (Settings → Camera keys): the engine pans on
  W/A/S/D and the shell moves Attack move to `F`, Stop to `H` and View
  headquarters to `J`.
- Settings for mouse-wheel zoom speed (default 3× the stock step) and a
  camera-rotation lock (on by default; middle-button drag and the rotate keys
  are ignored, a middle click still resets the view).
- Skirmish and campaign starts include a builder next to the headquarters;
  the tutorial still teaches training one.
- The debrief shows the difficulty the battle was played at and, after a win
  below Hard, points at the Difficulty row on the Deployment screen.
- Credits name the author.

### Changed

- Deployment screen modes read Tutorial, Skirmish, Campaign and Challenges;
  the OPPOSITION row is DIFFICULTY with Easy, Normal and Hard; the main-menu
  tagline, loader and field manual say the game is single-player.
- Every unit, structure, faction, difficulty and battlefield description is
  rewritten as plain information (role, strengths, weaknesses, requirement)
  instead of slogans; Jackal build labels are "Build X" like the Combine's.
- Headquarters produce the builder and infantry only; the Vector and Mongrel
  come from the Vehicle Plant and Chop Shop. Builder menus list economy and
  production structures on the first row and defenses on the second.
- Shells and rockets follow a moving target (`FlightPathAdjustDistPerSecond`
  on the projectile objects) and fly faster; artillery keeps a slow, dodgeable
  arc.
- Idle units and attack-move now engage enemy structures
  (`AutoAcquireEnemiesWhenIdle = Yes ATTACK_BUILDINGS`); before, only base
  defenses were attacked without an explicit order.
- Right-button panning starts only after the pointer leaves the click
  tolerance (now 20 game pixels), so a quick right-click with some hand motion
  is still an order.
- Trackpad wheel deltas below one notch are accumulated instead of truncated
  away, so two-finger scrolling zooms.
- Comma, period, minus, equals, brackets, slash and the keypad reach the
  engine (the rotate keys never worked in the browser).
- Home (camera reset) restores the zoom as well as the angle.
- The web page never navigates away on a two-finger swipe during a right-drag
  (`overscroll-behavior: none`), and closing or leaving the page during a
  battle asks first.

### Fixed

- Cancel construction did nothing: the under-construction window in
  `ControlBar.wnd` did not forward its button to the command bar.

## [0.1.3] - 2026-09-09

### Changed

- The desktop-required notice is a designed full-screen page: it escapes the
  16:9 game frame on portrait phones, presents the address in its own box with
  a share or copy action, and keeps the continue option as a quiet link.

## [0.1.2] - 2026-09-09

### Added

- Phones and touch-only devices see a desktop-required notice before anything
  downloads, with a copyable address and a session-scoped "Continue anyway";
  `?desktop=1` skips the gate. A tablet with a mouse or trackpad passes.

## [0.1.1] - 2026-09-09

### Added

- Link previews and site polish: Open Graph and Twitter card tags, a social
  preview image, SVG and PNG favicons, a web manifest, `robots.txt` and a
  styled 404 page; the stager takes `--public-url` for the absolute links.
- A release-driven deploy workflow (`deploy.yml`): publishing a GitHub release
  builds the tagged engine, stages the release bundle and deploys it to
  production.

### Changed

- Browser builds always use the Emscripten zlib port; a fresh machine no
  longer compiles a second zlib that collided with the FreeType port at link.
- The Vercel project is connected to the GitHub repository for commit
  metadata, with git-triggered builds disabled; repositories carry
  descriptions, topics and the play URL.

## [0.1.0] - 2026-09-09

First public release: <https://warpowers.vercel.app>. Source is tagged
`v0.1.0` in the root, engine and DXVK repositories.

### Added

- Open-source readiness: a first-time-visitor README, a contributor guide
  with the complete toolchain and gate list, a documentation index, a
  release process (`RELEASING.md`), a testing guide, a code of conduct, a
  security policy, issue and pull-request templates, `.editorconfig`, and
  GitHub Actions workflows for the gate list and a scheduled WebAssembly
  build (Actions remain disabled until the public release).
- Six engine switches in `GameData.ini`, parsed by `GlobalData.cpp` with the
  retail behaviour as each default: `RallyPointModel` (`SCMNode`),
  `RallyPointLineTexture` (`EXLaser.tga`),
  `DozerResumesAbandonedConstruction` (`No`), `MapPlacedHarvestersAutoGather`
  (`No`), `CommandButtonAvailabilityCues` (`No`) and `MusicRotation` (empty).
  The fork no longer hard-codes War Powers asset names or behaviour; the War
  Powers values live in the dataset.
- A dedicated rocket projectile model (`WPRKT01`); the content generators now
  fail closed when two assets would share a name.
- `tools/README.md`, shared `tools/wp_tga.py` and `tools/wp_w3d.py` helpers,
  and `argparse` interfaces on every tool.
- September polish push: 16:9 command layouts with selected-unit information,
  production queue, deployment previews, a field manual and construction
  notices; live training guidance with requirement checklists, lost-builder
  recovery and a full-sequence overview; all seven authored missions open
  from the start with recommended story order; an optional JSON backup of
  the operation record with non-destructive merge; browser-local settings,
  key remapping, channel audio, pause ownership and an IDBFS checkpoint slot
  with compatibility checks; a supply economy with physical haulers, one
  signature power per faction, a paid AI economy with retaliation and supply
  raids; original painted models for the whole 41-model roster, damaged and
  wreck variants, an environment kit, a menu panorama and 44 rendered
  portraits; a browser dependency inventory with bundled notices and a source
  record in every stage.

### Changed

- The seven base-kit models (Meridian Command Center, Power Array, Vehicle
  Plant and Fabricator; Jackal Command Post, Chop Shop and Rigger) are built
  by `tools/blender/build_polish.py` from `tools/blender/base_kit.py` with
  their original palette and painted recipe, so `build_polish.py --check`
  reproduces all 54 catalog models byte-for-byte; the four kit scripts and
  `legacy_contracts.py` are retired. Parts the old exports had rotated about
  the world origin through a Blender operator-state leak (the Command Post's
  crates, tarp and tower roof; the Rigger's crane arm; the Chop Shop's roof
  and sign) sit at their authored positions again.
- The diagnostic harness (scripted self-play, click tests, review scenes) is
  compiled only with the CMake option `WP_HARNESS=ON` (`wasm-harness`
  preset); production builds ignore its variables. The engine traces stay in
  every build behind runtime environment switches, and the shell forwards
  diagnostic URL parameters only with `?debug=1`.
- The licensing overview is `LICENSING.md` again; the root `LICENSE` file is
  the MIT text that GitHub's license detection reads.
- Documentation restructured: `docs/README.md` indexes everything; the
  release checklist became `RELEASING.md`; `parity.md` folded into the
  roadmap; verification notes, the polish assessment and the engine bring-up
  log moved to `docs/history/`; `engine-notes.md` keeps only durable engine
  knowledge; `perf.md` keeps budgets and method.
- The local server runs on `http://localhost:8322` by default and reports an
  occupied port with a clear error instead of suggesting a second origin;
  browser storage is per origin.

### Removed

- `refs/` (6 MB of prototype-era Quaternius FBX references that nothing
  used; provenance stays in `ASSETS.md` and `CREDITS.md`, files stay in git
  history), the prototype-era tools `wp_metal_spy.m`, `spike_export.py`,
  `genicons2.py`, `build_vector.py`, `convert_mongrel.py` and
  `convert_pack_units.py`, and the historical GPL `ExtrasMenu.wnd` copy
  (removed from the dataset on 2026-09-05; its provenance is recorded).

### Fixed
- The map-wide wind ambient now rides on one neutral, invisible emitter per map
  instead of both command centers, so the second copy is no longer rejected and
  retried every frame; `tools/validate_gameplay.py` enforces the emitter contract.
- `WP_VOLUME` is applied once, as the seed of the master slider, instead of also
  scaling the MiniAudio engine master (native runs with a value below 100 were
  playing at the square of the requested level).

- Retry after a defeat could crash the engine through mip-filter reference
  ownership, released texture storage and unchecked surface copies; sentence
  layout misread trailing ampersands and optional hotkey coordinates. All are
  covered by native sanitizer fixtures and renderer contract tests.
- Browser recovery no longer calls into a failed engine; the stager refuses
  to replace compiler output or repository directories.
- Wheeled vehicles steer correctly (`MinTurnSpeed`), attack-move enters
  targeting mode, and unavailable commands show a padlock instead of relying
  on grayscale alone.

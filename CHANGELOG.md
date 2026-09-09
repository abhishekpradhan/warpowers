# Changelog

All notable changes to War Powers are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Nothing yet.

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

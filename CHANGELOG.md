# Changelog

All notable changes to War Powers are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project has no
version numbers yet, so everything sits under *Unreleased* until the first
public build, whose build identifier will head the first release section.

## [Unreleased]

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

- Retry after a defeat could crash the engine through mip-filter reference
  ownership, released texture storage and unchecked surface copies; sentence
  layout misread trailing ampersands and optional hotkey coordinates. All are
  covered by native sanitizer fixtures and renderer contract tests.
- Browser recovery no longer calls into a failed engine; the stager refuses
  to replace compiler output or repository directories.
- Wheeled vehicles steer correctly (`MinTurnSpeed`), attack-move enters
  targeting mode, and unavailable commands show a padlock instead of relying
  on grayscale alone.

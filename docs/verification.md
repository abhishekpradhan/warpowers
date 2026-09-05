# Current polish verification

Local checks recorded 2026-09-05. This page distinguishes observed behavior
from diagnostic fixtures and from release checks needing independent people
or devices. These runs use a local staged WebAssembly build in the available
Chromium in-app browser on the development Mac.

## Automated local gates

- Web-state tests: malformed/blocked storage, settings bounds, actual command
  remapping, explicit-win progression, safe identifiers, time/map normalization.
- Packaging tests: repeatable hashes, complete content references and notices,
  UI versus save compatibility, engine-glue release identity, protected output
  paths, and rejection of an oversized candidate without replacing a working stage.
- Voice lint: 80 distinct events across 21 templates, no accidental shared pools.
- Content references: native model/texture/icon/window and operation metadata checks.
- Map validator: independently decodes all 17 shipped map binaries, evaluates
  seven mission success/failure/tie cases, checks actual native condition/action
  signatures, paid AI responses, supply/counter/budget contracts, and flood-fills
  traversable routes to units, caches and objectives with a cliff-clearance margin.

Run commands are in [CONTRIBUTING.md](../CONTRIBUTING.md). These checks do
not establish final balance or visual quality by themselves.

## Observed browser behavior

Build `16a02361cddb`:

- Main menu and deployment: original panorama, mode switching, tactical preview,
  assigned training faction and native deployment button all render and respond.
- Field Orientation: briefing opens, resumes the game, HQ selection works;
  queueing a Fabricator charges money and creates the unit. The objective advances
  to supply/power. The idle-builder key selects and centers the Fabricator.
- Exchange and Power Array: builder portraits, native tooltips, placement and
  construction progress work. The Exchange finishes and provides its small
  income stream.
- Checkpoint: browser storage writes successfully; full page reload exposes
  Resume checkpoint. Restored scene retains objects, construction, money and time.
  A case mismatch initially lost the mission identity; a subsequent engine fix
  canonicalizes portable save map names. That fix requires another round-trip check.
- Post-boot error UI: earlier integration failures visibly reopened the loader
  with a recovery message and diagnostics. Missing scenery Body modules and an
  overlong EM_ASM call were corrected; training then loaded successfully.

Build `7a05419481b2`, native diagnostic fixtures:

- Meridian supply: creates a completed power/depot fixture, then queues a Porter
  through native production. The produced truck carries four crates, delivers,
  and repeats. At 60 seconds, 20 crates were removed and income increased $1,100,
  including approximately $300 passive hub income. Harness reports PASS.
- Jackal Tunnel Ambush: invokes the native power at a revealed target after an
  explicit ready-state fixture. Five infantry spawn and the next-ready frame moves
  forward. Harness reports PASS. Construction/cooldown waiting and user targeting
  are separate input checks.

The supply harness initially selected an unrelated starting truck and failed to
complete the fixture depot's native creation lifecycle. Its corrected run tracks
the produced truck's producer ID and calls the same module completion hooks as a
finished building. The result above is from the corrected harness.

- Jackal supply: the produced Scavenger carries two crates and repeats the
  route. At 60 seconds, 12 crates were removed and income increased $740,
  including approximately $240 passive income. Harness reports PASS.
- Meridian Precision Strike: the native effect deals 550 damage to its target
  and advances the recharge frame. Harness reports PASS.
- A prolonged, undefended power fixture also ended in an actual AI assault and
  HQ destruction, displaying the native Defeat banner and a losing match result.

## Reproduce focused diagnostics

After staging and starting `tools/serve.py`:

- `/?map=Maps/WPTest.map&autotest=economy` — Meridian hauling.
- `/?map=Maps/WPTestJ.map&autotest=economy` — Jackal hauling.
- `/?map=Maps/WPTest.map&autotest=powers` — Precision Strike.
- `/?map=Maps/WPTestJ.map&autotest=powers` — Tunnel Ambush.

The diagnostic report is visibly retained in the page; verbose frame logs cannot
roll its result out of view. Ordinary play shows no diagnostic report. Diagnostic outcomes do not write the player’s persistent operation record. Avoid
`debug=1` unless tracing a specific engine problem: it produces verbose logs.

## Remaining candidate checks

Candidate `6375e6bfb189` contains the final roster/portraits, powered Meridian
defenses, save-map identity/control-bar corrections and fixed native mission
result assertions. It compiles and passes all local static gates; its staged
payload is 66,729,367 bytes. Six web-state and six packaging tests pass.

The final rendered portrait and model contact sheets were visually reviewed.
Browser automation is currently blocked by the development Mac lock screen;
manual unlock is required to resume the checks below. No final play-readiness
claim is made while those checks are pending.

Native mission end-to-end regressions, final in-engine art review, input-driven unit/combat
coverage, final save/restore identity, fullscreen/settings recovery, a crowded
performance run and final repository push/clone verification are in progress.
The separate human/browser/network release matrix remains in
[publish-checklist.md](publish-checklist.md).

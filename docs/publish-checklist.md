# War Powers — release checklist

Updated 2026-09-05. This checklist does not authorize deployment or changing
repository visibility. The owner authorized implementing the polish plan,
preparing the private repositories and committing/pushing work. A public
release remains a separate decision (D013).

Check an item only with evidence for the current candidate. Earlier local
boot and Safari smoke results are useful history, not certification of the
new art, HUD, scenarios or save system.

## Local candidate

- [x] Web settings/progress tests, including corrupt or blocked storage,
      duplicate key bindings, invalid mission records and bounded options.
- [x] Packaging tests: deterministic content paths, references and sizes,
      bundled notices, save compatibility and output-directory protection.
- [x] Voice ownership lint and content model/texture/icon/window references.
- [x] Independent binary validation of all 17 maps, seven objective
      success/failure/edge cases, native script signatures and faction/AI rules.
- [ ] Browser: boot → deployment → battle → result → retry/menu, both factions.
- [ ] Input: selection, right-click orders, attack-move, groups, rally,
      build placement, queue cancel, pause and fullscreen.
- [ ] Supply: train, gather, return, credit income, deplete/reassign and raid.
- [ ] Powers: prerequisites, scouted target, visible warning/effect and cooldown.
- [ ] Operations: tutorial stages, changing objectives, deadlines, defeat,
      optional targets, debrief, unlock and replay.
- [ ] Checkpoint saved durably, reload/resume restores battle, incompatible
      or unavailable storage produces a recoverable explanation.
- [ ] Original asset lifecycle and combat readability verified in-engine.
- [ ] Final size budget, boot and crowded-battle performance recorded in perf.md.
- [ ] Root/engine/DXVK commits pushed in child-first order; pinned commits
      reachable remotely; recursive checkout and local checks reproduce.

## Human and hardware checks before release

- [ ] A full human-played match on each difficulty and each faction; record
      confusing controls, first contact, viable openings and recovery.
- [ ] Full training and campaign playthrough without coaching.
- [ ] Audio listening pass: speech intelligibility, repetitions, volume balance,
      weapon/impact timing and critical text alerts.
- [ ] Safari full match including saving and fullscreen. Earlier build booted.
- [ ] Firefox boot and full match including saving and fullscreen.
- [ ] A second, lower-end desktop; document OS/GPU/browser and actual limits.
- [ ] Crowded 30–45 minute stress run, restart/redeploy, memory and frame timings.

## Distribution and source

- [x] Stager packages credits, asset ledger, license map, root code license,
      engine license, browser-renderer license and font notice.
- [x] Hashed engine/data/UI URLs permit immutable caching; HTML/build metadata
      revalidate. Local server and prepared hosting headers reflect this.
- [x] Final ledger/registry agrees with shipped files, generator versions and
      remaining imported music/font notices.
- [ ] Final source audit excludes credentials, private saves, local SDK paths,
      proprietary game assets and misleading upstream project links.
- [ ] Preserve the exact corresponding engine/renderer source and build
      instructions for the distributed binary, plus required license notices.
- [ ] Verify final public names/branding and the chosen domain before release.

All maintained repositories currently remain private under the owner's
account: `warpowers`, `warpowers-engine`, `warpowers-dxvk`. The former
`warpowers-dvijoke` is archived; its history and source are vendored into the
root. Follow the owner's eventual publication choice rather than creating
an organization or transferring repositories automatically. Update source
links/submodule URLs only when the destination is known and accessible.

Upstream push URLs stay disabled. Inherited GitHub Actions stay disabled;
ordinary pushes do not deploy anything. See [WORKSPACE.md](WORKSPACE.md).

## Hosting after explicit authorization

- [ ] Protected preview of the generated `webstage/` only.
- [ ] Verify JS/WASM content types, compression, cache hit/revalidation
      behavior and current credits/source links at the actual URL.
- [ ] Measure first and repeat visits on a real network against the ≤20s
      boot target; repeat the browser matrix against that candidate.
- [ ] Confirm publication settings, public source availability and final Play URL.

No account or hosted telemetry is required for the game. Debug boot reports
are opt-in (`?debug=1`) and local diagnostics can be copied from Settings.

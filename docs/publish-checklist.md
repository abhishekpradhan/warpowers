# War Powers — release checklist

Updated 2026-09-05. This checklist does not authorize deployment or changing
repository visibility. The owner authorized implementing the polish plan,
preparing private repositories and committing/pushing work. A public release
remains a separate decision (D013).

Current local playtest candidate: `66f4e32fcfab`, 66,740,374 bytes. Build, web,
packaging and content gates pass. Bounded observations from earlier candidates
are explicitly identified in [verification.md](verification.md). A checked
fixture is evidence for that fixture; broader release categories stay open
where only some requirements have been exercised.

## Completed local checks

- [x] `66f4e32fcfab`: full WASM build, 17 web-state/record tests, six packaging
      tests and voice/content/map gates pass. Metadata rejects access prerequisites.
- [x] A 0/4 campaign record can launch operation 4 through the journal, deployment
      and briefing into its battlefield. Assigned-side operation navigation
      hides the alternate action and returning to Skirmish restores both sides.
- [x] Actual file-picker restore merges better records without losing existing
      results; malformed input leaves them intact. A real downloaded JSON file
      restores successfully, and the merged results survive full reload.
- [x] Two open game tabs share new record entries; legacy map-key wins survive
      canonical-key losses. Restoring an older backup preserves newer results,
      and the final downloaded file contains canonical IDs without duplicate wins.
- [x] `1df03a19fdd9`: menu frame/panel removed, explicit disabled-command and
      faction-deployment padlocks, web disabled styles; final WASM build and
      web/packaging/content gates pass. `15907462d540` normal training verifies
      prerequisite/funds locks, affordability recovery and queue cancellation.
- [x] `1df03a19fdd9`: a normally built Directorate keeps its recharge sweep and
      countdown visible, loses the lock at POWER READY after natural recharge,
      accepts ground targeting and restores the lock on the next cooldown.
- [x] `2a5fb93551f9` passes the full WASM build, six web-state tests, six packaging
      tests and 16 native keyboard cases.
- [x] Voice lint, model/texture/icon/window references and operation metadata pass.
- [x] Independent validation of all 17 map binaries, seven mission branch/edge
      cases, native script signatures and faction/AI/route contracts passes.
- [x] `6375e6bfb189`: seven native mission wins, seven native failures and three
      HQ-loss failures assert the actual result callback; no mission-check failures.
- [x] `6375e6bfb189`: native power fixtures deal 550 damage for Precision Strike
      and spawn five infantry for Tunnel Ambush.
- [x] `6b10` steering-fix candidate: produced and opening haulers gather/deliver
      for both factions; measured income includes passive income and both trucks.
- [x] `6375e6bfb189`: normal training production/construction → save → full reload
      → Resume restores the correct mission/stage, 3:20 time, $3,500, structures,
      Exchange foundation and HUD; the resumed Exchange then completes.
- [x] `6b10`: normal-menu diagnostic training → debrief → Victory report → Retry
      starts a fresh same-faction training match.
- [x] `6b10`: fullscreen/Settings/Escape recovery and P-pause ownership work;
      dismissing Settings preserves the paused 10:47 clock until P resumes it.
- [x] `db2a99b4c142`: Control+1 assigns nine units with labels; deselecting and
      pressing bare 1 recalls nine; right-click orders move the selected army.
- [x] `db2a99b4c142`: Jackal Chop Shop produces two Mongrels; active queue cancel
      refunds the cancelled entry while one queued unit remains pending.
- [x] `db2a99b4c142`: Jackal native art scene displays 22 fixtures with zero missing
      models, visible structures/infantry/vehicles/two airframes and distinct silhouettes.
- [x] `a89d614eaa5c`: Q selects seven Jackal units; Attack Move plus a revealed
      ground target moves them with selection retained. I selects/centers the
      original Rigger and displays eight construction portraits.
- [x] `a89d614eaa5c`: ordinary builder placement finishes a Watchpost after visible
      progress; the centered “Construction complete.” toast appears visually and
      in the accessibility tree.
- [x] `a89d614eaa5c`: after 120 seconds natural recharge, Den → Tunnel Ambush →
      open explored ground spawns five infantry (8 → 13) with selection retained.
- [x] `a89d614eaa5c`: Settings remaps idle worker I→J; after Restart the native
      J hint appears and J selects/centers the Fabricator.
- [x] `9294283038c0`: after 150 seconds natural recharge, Precision Strike accepts
      empty explored ground through its normal button, shows an impact scorch,
      retains Directorate selection, clears targeting and starts the next cooldown.
- [x] `9294283038c0`: normal training save → full reload → Resume restores the
      correct briefing/stage, 2:46 time, $4,850, one Fabricator, two structures, 16 power,
      HUD and remapped J hint; this run restores a completed Power Array.
- [x] `2a5fb93551f9`: visible native RECHARGING countdown reaches POWER READY;
      the heading fits, another ground-targeted strike fires and cooldown restarts.
      Q selecting the army restores the ORDERS heading.
- [x] Commander-trial navigation passes: `9294283038c0` Jackal Hostile Takeover
      menu → deploy → diagnostic win/debrief → Victory report → Continue returns
      to the main menu; final `2a5fb93551f9` Meridian Glass Rampart reaches the
      same report and Change Battlefield returns to the correct deployment.
      Final trial preview titles/summaries fit; full briefings remain intact.
- [x] Meridian native art review on `db2a99b4c142` / `9294283038c0` displays 23 fixtures
      with zero missing models, all roster rows, steering vehicles and flying aircraft.
      The crowded `6b10` scene shows firing/explosions/smoke/scorches and expiring wrecks.
- [x] Current local stage is below the enforced 64 MiB combined size limit.
- [x] An isolated one-minute 120-unit attack-move fixture has recorded hardware,
      resolution, render/logic cadence and WASM heap-capacity measurements in perf.md.
- [x] An earlier pushed snapshot reproduces from a fresh recursive GitHub clone:
      tests/gates, documented configuration, 1,279-step clean engine build and staging.
- [x] Initial completed polish snapshot pushed: root `0ab5819`, engine
      `05c81c9908d95f6428b14a96935694539b6c1b9d`, DXVK `538cb703`.
- [x] Independent checkout at those pins passes all tests/gates, incremental
      WASM build and staging after its earlier clean build. Tree clean; recursive
      pins resolve. Candidate `a50ecbb361a0` is 66,734,559 bytes. This independent
      artifact was not browser-tested; browser evidence belongs to the primary
      candidates recorded in verification.md.

## Remaining local candidate coverage

- [ ] Finish input coverage: rally, the remaining remapped actions and intended
      selection/order/placement interactions. Attack-move and idle-worker remapping
      now have observed native-input coverage.
- [ ] Supply depletion, reassignment and raids under normal play, beyond the
      successful gathering/delivery fixtures.
- [ ] Complete power presentation/prerequisite checks beyond the successful
      both-faction targeting and recharge flows: capture the transient warning
      and observe the native POWER REQUIRED condition. Ready/cooldown headings
      now have visible final-candidate evidence. The initial unsuccessful Precision
      Strike attempt was not reproduced and is no longer an unresolved defect.
- [ ] Tutorial stages, changing objectives, deadlines, optional targets, debrief,
      completion recording and replay through ordinary play, beyond scripted
      branch regressions. Mission access never requires a previous result.
- [ ] Exercise unavailable/incompatible storage and recoverable explanations in
      the browser, beyond successful save/resume/construction completion and
      automated storage-state tests.
- [ ] Complete the remaining both-faction asset lifecycle/combat-state coverage;
      the successful roster and crowded-scene observations do not cover every state.

Both final browser tabs reported empty console-error lists. That
observation does not replace the untested paths above.

## Human and hardware checks before release

- [ ] A full human-played match on each difficulty and each faction; record
      confusing controls, first contact, viable openings and recovery.
- [ ] Full training and campaign playthrough without coaching.
- [ ] Audio listening pass: speech intelligibility, repetitions, volume balance,
      weapon/impact timing and critical text alerts.
- [ ] Safari full match including saving and fullscreen. Earlier build booted.
- [ ] Firefox boot and full match including saving and fullscreen.
- [ ] A second, lower-end desktop; document OS/GPU/browser and actual limits.
- [ ] Controlled crowded 30–45-minute run, restart/redeploy, process memory and
      frame timings. The one-minute isolated sample and approximately 11-minute
      battle observation do not satisfy this soak requirement; 512 MiB WASM heap
      capacity is not process RSS.

## Distribution and source

- [x] Stager packages credits, asset ledger, license map, root code license,
      engine license, browser-renderer license and font notice.
- [x] Hashed engine/data/UI URLs permit immutable caching; HTML/build metadata
      revalidate. Final local HTTP checks return 200 with correct WASM/JavaScript
      types, immutable one-year asset caching and no-cache HTML/build metadata.
- [x] All 471 final manifest entries, engine files and font match declared hashes
      and lengths.
- [x] Ledger/registry agrees with shipped files, generator versions and remaining
      imported music/font notices.
- [x] Final bounded root/engine hygiene review covers 16 changed text files
      (638,130 bytes): no high-confidence credential patterns, absolute developer
      paths, build/save/env artifacts, missing local links or removed attribution;
      root engine gitlink matches the pushed engine commit. This supplements the
      prior tracked-text scan and does not certify all repository history.
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

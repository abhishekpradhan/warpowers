# War Powers — current roadmap

Updated 2026-09-05. The owner authorized implementation of the product
polish plan on September 4, including repository preparation and ordinary
commits/pushes. Publication and hosting remain separate decisions. The
engine and swappable dataset architecture remain the foundation (D018).

## Current local playtest work

Candidate `6631b2c96367` passes the release WASM and native macOS builds,
28 web-state/guidance/recovery tests, nine packaging tests and all
content/gameplay/voice gates. Focused regressions pass 16 keyboard cases,
32 sentence-text cases, 71 mip-filter checks, 40 surface-copy checks in each
of the manual and GLI paths, and 27 renderer resource checks.
The latest feedback pass adds stronger active/disabled command contrast,
live training requirement checklists, lost-builder recovery advice and an overview of
all steps. Normal training reaches all five guidance stages; collapse/reopen
and 125% overlay text checks pass. Development now uses one standard server
at `http://localhost:8322`; the redundant QA listener was stopped.
The Retry investigation repaired texture/surface ownership, bounded mip
copies and sentence-text access. The final release candidate completed two
consecutive eight-minute training matches, native defeat reports and Retry
transitions in one runtime with tracing disabled. The ordinary web debrief
also continued through the native report and Retry to a fresh match. A
separate sanitizer candidate passed a three-minute match and Retry; focused
regressions reproduce the prior failures and pass with the repairs.
Native evidence spans this candidate and preceding controls, faction-power,
mission and hauling runs;
[verification.md](verification.md) records which build exercised each flow.

Review before merging to main also fixed failure-screen handling that could
re-enter an already broken engine, and staging destinations that could replace
compiler output. Both fixes have regression coverage; the engine quick-start
now agrees with the standard server URL.

The first player-feedback follow-up removes the redundant main-menu boxes and
adds explicit padlock cues for unavailable in-match commands.
Normal training checks cover prerequisite/funds locks, restored affordability
and queue cancellation with a refund.

The next follow-up makes all seven authored missions immediately available:
story order is recommended, and losing browser data cannot gate content in a
game without accounts (D023). Authored missions show only their assigned
faction's deployment action; skirmish offers both sides. An optional JSON
operation-record backup carries completions and best times through a
non-destructive merge, separate from settings and battle checkpoints. Browser
checks confirm that a 0/4 campaign record can launch operation 4, assigned-side
navigation restores both choices in skirmish, record files merge without losing
better results, malformed files leave records intact, and a downloaded backup
restores successfully with the merged results surviving a full reload.
Two open game tabs share merged records without losing newer completions;
legacy map IDs preserve their winning results alongside canonical mission IDs.

| Area | Implemented | Verified locally / remaining work |
|---|---|---|
| Command experience | 16:9 layouts, selected-unit information, queue, deployment previews, manual, objectives and construction notices | Training selection/production/placement, nine-unit group assignment/recall, whole-army right-click movement and Jackal production/cancel/refund observed; attack-move targeting, idle-Rigger shortcut and fresh Watchpost construction notice pass on a89d614eaa5c; remaining input matrix pending |
| Entry and solo content | All seven authored missions open immediately, recommended story order, assigned-faction deployment, native objectives and persistent operation record | All seven native wins, seven failures and three HQ-loss failures passed actual result callbacks; training Retry, Jackal trial Continue → menu and Meridian trial Change Battlefield → deployment pass; trial previews fit; 0/4 campaign record can launch operation 4; human walkthroughs and normal completion/replay checks remain |
| Economy and factions | Finite physical supplies, hauling trucks, independent Jackal power, faction costs/counters and one power per faction | Both hauling fixtures pass after the steering correction; native 550-damage Precision Strike and five-unit Tunnel Ambush pass; both powers pass real targeting after natural recharge (Jackal 120s, Meridian 150s); ready/cooldown headings and another strike pass on the final candidate; depletion/reassignment/raids, transient warning and POWER REQUIRED presentation remain |
| Opponent and maps | Paid economy/production, composition responses, supply raids, scenery and route identities | All 17 map binaries pass cliff-clearance route checks and an AI HQ assault was observed; full difficulty/faction balance matrix remains |
| Original art | All 41 roster models original; lifecycle/ownership/aiming contracts, environment kit, panorama and 44 portraits | Export/import, hierarchy, texture and portrait checks pass; Meridian 23 / Jackal 22 fixture scenes have zero missing models and distinct silhouettes; steering, flight and several combat/wreck states observed; exhaustive lifecycle coverage remains |
| Product durability | Settings, remapping, channel audio, pause ownership, IDBFS checkpoint, compatibility checks, recovery UI and optional operation-record JSON backup | Full reload/resume restores training identity, stage, time, economy, construction and HUD, including resumed Exchange completion and a later completed Power Array; fullscreen/Settings recovery, explicit pause ownership and I→J remapping pass; record download/restore/merge, malformed-file rejection and reload persistence pass; broader storage/error/input matrix remains |
| Performance and distribution | Hashed paths, stable build IDs, bundled notices, registry and enforced 64 MiB staging limit | Current candidate 6631b2c96367 stages at 63.681 MiB; isolated 120-unit attack-move fixture holds approximately 60 render / 30 logic for one minute on M1 Max/64 GB at Balanced; long soak, lower-end hardware and network/browser matrix remain |
| Open-source preparation | Root/engine/native-renderer contribution/build docs, fork routing and protected upstream remotes | Initial completed polish root 0ab5819 / engine 05c81c9908d95f6428b14a96935694539b6c1b9d / DXVK 538cb703 are pushed; independent checkout passes tests, gates, incremental build and staging after its earlier 1,279-step clean build; recursive pins, manifest hashes and bounded hygiene review pass |

The [polish plan](product-polish.md) defines intended player outcomes; the
[publish checklist](publish-checklist.md) retains independent release gates.
A generated file, static validator or focused fixture does not establish
public-release readiness. The performance measurement reports WASM heap
capacity, not browser process RSS; see [perf.md](perf.md).

## Established foundation

The browser engine boots without retail assets and supplies selection,
orders, fog, construction, combat, a minimap, production and match results.
The dataset supports Meridian Combine and Jackal Front (D017), while the
native macOS port remains useful for engine development. Earlier progress
and measurements are preserved in Git history and the engine worklog.

## Before a public release

- Complete remaining input/lifecycle checks, the transient power warning and
  the POWER REQUIRED condition without treating partial coverage as a full pass.
- Finish operation-record download/restore/replay browser checks, including
  repeated imports and preservation of existing completions and best times.
- Human training/campaign walkthroughs and full matches on every difficulty
  and faction, with independent balance and control feedback.
- Audio listening/mix review, Safari/Firefox and lower-end desktop testing,
  a controlled crowded 30–45-minute run and real-network loading measurements.
- Publish source or hosting only when authorized; retain the verified
  corresponding source and notices for the chosen release.

Multiplayer, Iron Pact, a larger campaign, superweapons and a broad
progression tree remain separate scope decisions.

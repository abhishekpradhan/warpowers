# Roadmap

Updated 2026-09-07. War Powers is a browser port of the GeneralsX engine with
its own bundled dataset (decision D018); the two-faction game is the release
scope (D017). This page says what ships today, what is being worked on, what
comes after, and what is deliberately out of scope. Dated evidence for the
completed rows is in [history/2026-09-verification.md](history/2026-09-verification.md).

## What ships today

| Area | Implemented | Acceptance bar still to meet |
|---|---|---|
| Factions | Meridian Combine and Jackal Front with distinct power, economy and combat characteristics; one signature power each (Precision Strike, Tunnel Ambush) | Several viable openings and understandable counterplay in human matches |
| Roster | Builders, haulers, recon, gun truck, tanks, artillery; four infantry roles per faction; two aircraft per faction; headquarters, production, supply, technology and layered defence structures — all 41 models original | Every command, turret/muzzle, cargo and damage state exercised in play; equal-budget counter encounters |
| Skirmish | Five layouts, each from either faction's side, three difficulties; an opponent that builds, expands, escalates, defends, retaliates and raids the economy | Full difficulty × faction balance matrix |
| Authored content | Field Orientation training, four campaign operations and two commander trials, all open immediately (D023); native objectives, deadlines, warnings, failure and replay | Uncoached human playthroughs |
| Command experience | 16:9 layouts, selected-unit information, production queue with cancel/refund, placement previews, attack-move, guard, stop, rally points, control groups, idle-worker shortcut, remappable keys, field manual, objective clock, live training guidance | The remaining input matrix (rally, remapped actions, placement edge cases) |
| Economy | Finite physical supply caches, hauler trucks, hub income, faction-specific costs and counters | Depletion, reassignment and supply raids under normal play |
| Persistence | Browser-local settings, one checkpoint slot (IDBFS) with compatibility checks, an operation record with optional JSON download/restore/merge | Unavailable or incompatible storage explained in the browser |
| Audio | Per-unit voice pools, weapon and ambient effects, announcer, six attributed music tracks, separate channel volumes | A listening and mix pass |
| Distribution | Content-hashed immutable assets, stable build identifiers, bundled credits and dependency notices, a source record, a 64 MiB staging limit | Real-network boot measurement; hosting |
| Diagnostics | Scripted self-play modes, click tests and review scenes in a separate harness build; runtime-gated engine traces in every build; focused native fixtures; content, gameplay and voice validators | — |

`tools/validate_gameplay.py` decodes the shipped map binaries and checks
mission branches, script signatures, faction contracts, paid AI responses and
opening budgets; `tools/check_content.py` validates model, texture, icon and
window references and writes the asset registry; `tools/lint_voices.py`
checks voice ownership. They complement browser and player verification; they
do not replace it.

## Now

- **0.1.0 is live** at <https://warpowers.vercel.app> (released 2026-09-09;
  source public, CI and the release-driven deploy workflow enabled). The next
  patch batch collects what the public build and the playtests below surface:
  the builder's command order (the Exchange sits in the fifth slot although
  the training asks for it first), structure portraits that read alike until
  hovered, and the one-tick lag of the selected-unit panel behind the orders bar.
- **Human playtests:** a full match on every difficulty and faction, and the
  training and campaign missions without coaching; record confusing controls,
  first contact, viable openings and recovery.
- **Remaining verification:** the rest of the input matrix, supply depletion
  and raids, the transient power warning and the POWER REQUIRED condition,
  storage-failure explanations, both-faction asset lifecycle coverage.

## Next

- Browser matrix: full matches including saving and fullscreen in Safari and
  Firefox; a second, lower-end desktop with its OS, GPU and browser recorded.
- A controlled 30–45 minute crowded run with restart and redeploy, measuring
  process memory and frame timings (see [perf.md](perf.md)).
- Repeat-visit and lower-end-machine boot numbers over a real network; the
  first-visit figure is 3.3 s on a desktop against the 20-second budget (see
  [perf.md](perf.md)).
- Audio listening pass: intelligibility, repetition, balance, impact timing.
- Balance pass from match evidence, then AI variety where the evidence asks
  for it.
- A purchased domain in front of the Vercel address (D026).

## Before 1.0

- A hosted build with its corresponding source reachable from the credits
  page, following [RELEASING.md](../RELEASING.md).
- Trademark and domain check for the name (D006) and final public branding.
- Presentation work the art pass deferred: construction build-up animation,
  rotor and tread motion, bespoke structure destruction, richer terrain
  transitions, weapon impact effects.
- Accessibility: colourblind-safe checks on the final palette, UI scale
  options, integrated-GPU performance.
- A stable checkpoint format across builds, or an explicit migration story.

## Not planned

- Multiplayer, replays and observer mode. The engine is lockstep-native and
  the merged web branch carries a WebRTC transport, but a lobby service and
  the deterministic-replay verification it needs are out of scope for now.
- The Iron Pact third faction (designed in [creative.md](creative.md), built
  only after the two-faction game is finished; nothing about it ships).
- A larger campaign, superweapons or a broad promotion/progression tree.
- Mobile or touch input (D008).
- Accounts, cloud saves or telemetry (D023): everything stays in the browser.

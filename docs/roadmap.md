# War Powers — current roadmap

Updated 2026-09-05. The owner authorized implementation of the product
polish plan on September 4, including repository preparation and ordinary
commits/pushes. Publication and hosting remain separate decisions. The
engine and swappable dataset architecture remain the foundation (D018).

## Product polish in progress

| Area | Implemented | Verification / remaining work |
|---|---|---|
| Command experience | 16:9 layouts, selected-unit information, production queue, deployment previews, field manual and objective/guidance overlays | Training deployment, selection, native production and construction observed; final input matrix pending |
| Entry and solo content | Field Orientation, four connected operations, two commander trials, native objective triggers and persistent operation record | Binary objective success/failure/edge cases pass; input walkthroughs in progress |
| Economy and factions | Physical supply trucks and finite caches, power-independent Jackal, distinct armor costs/timings, counters and one power per faction | Supply/power native diagnostics passed; final wheel-locomotor harvesting and user targeting checks pending |
| Opponent and maps | Paid economy/production, bounded composition responses, supply raids, authored scenery and route identities | All 17 map binaries pass cliff-clearance route checks; an AI HQ assault was observed; full match matrix pending |
| Original art | All 41 roster models original; lifecycle/ownership/aiming contracts, environment kit, panorama and 44 rendered portraits | Export/import, hierarchy, texture and portrait checks pass; final in-engine readability review pending |
| Product durability | Settings, key remapping, channel audio, pause ownership, IDBFS checkpoint, compatibility checking and visible error recovery | Web-state/packaging tests and initial durable checkpoint round-trip pass; final restore-identity/fullscreen checks pending |
| Distribution | Content-hashed paths, stable build IDs, credits/notices in staged bundle, asset registry and staged checks | 63.638 MiB bundle passes enforced 64 MiB limit; fresh recursive clone builds and stages successfully |
| Open-source preparation | Root/engine/native-renderer build and contribution docs, fork routing, protected upstream remotes | Provenance and bounded source checks pass; all three feature branches pushed, remote gitlinks verified by recursive clone |

The [polish plan](product-polish.md) defines the intended player outcomes.
The [publish checklist](publish-checklist.md) records the independent release
gates. A generated file or passing static validator alone does not mean a
feature has passed a player test.

## Established foundation

The browser engine boots without retail assets and supplies selection,
orders, fog, construction, combat, a minimap, production and match results.
The dataset supports Meridian Combine and Jackal Front (D017), while the
native macOS port remains useful for engine development. Earlier progress
and measurements are preserved in Git history and the engine worklog.

## After this polish pass

- Human full matches on every difficulty and independent balance feedback.
- Safari/Firefox and lower-end desktop verification, crowded late-game
  performance, and real-network loading measurements.
- Public source/hosting work only when authorized; retain source and notices
  for the exact distributed build.
- Multiplayer, Iron Pact, a larger campaign, superweapons and a broad
  progression tree remain separate scope decisions.

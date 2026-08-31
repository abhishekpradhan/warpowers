# Web performance — budgets & measurements (updated 2026-08-31)

Current numbers are Phase 5 measurements (M-series Mac; boot via permanent
`performance.mark` instrumentation in web/index.html, frame capacity via
MainLoop pump-rate). The 2026-08-23 baseline is kept at the bottom.

## Measured (2026-08-31)
- **Bundle: 55MB staged** (11MB wasm + ~44MB gamedata — the 6-track music
  rotation added ~20MB by design). CDN brotli roughly halves wire size;
  verify on the preview deploy (publish-checklist §5).
- **Boot: 5.5s cold** (page load → engine main loop; 165ms engine dl /
  214ms data / 5.2s init) against the ≤20s budget.
- **Frame capacity: flat 60/s** through a BRUTAL match's raider/pack/assault
  phases; logic locked at 30. Late-game mega-army stress still open
  (checklist §2), as is the mid-laptop run (checklist §1 second machine).
- Hidden tabs auto-pause (rAF suspension) — product behavior, documented in
  engine-notes.

## Budgets
- Bundle ≤ 64MB staged (re-baselined 2026-08-31: the old ≤35MB predates the
  music import; wasm share ≤ 12MB unchanged). Watch texture growth.
- Boot ≤ 20s on a mid laptop from a real network — MET locally; CDN
  numbers pending the preview deploy.
- Steady 60 render / 30 logic on a mid laptop at 1024×768 — M-series MET;
  mid-laptop pending second machine.

## Follow-ups
- Hashed asset filenames for immutable CDN caching (docs/hosting.md).
- Known perf debt: money-readout font surface churn (no measured symptom).

## Baseline for contrast (2026-08-23, pre-shell)
26.5MB bundle, ~25–40s deploy-click boot dominated by synchronous engine
init, 30–60 fps pane rendering. Everything above supersedes it.

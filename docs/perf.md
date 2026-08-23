# Web performance baseline & budgets (2026-08-23)

Observed on the dev machine (M-series Mac, localhost serving, in-app browser
pane). Numbers are coarse stopwatch/log observations — proper marks belong in
the page (`performance.mark`) as a follow-up.

## Observed today
- Bundle: 26.5MB staged (11MB wasm, ~15MB gamedata incl. audio + 512px
  textures). Fetch on localhost: seconds; real-world 20Mbps: ~11s — fine
  with the byte-accurate progress bar.
- Boot (DEPLOY → match visible): ~25–40s. Dominated by the synchronous
  engine init inside main() (INI parse + asset load on the main thread) —
  the tab freezes during it, which is why the loader hands off with a
  "Starting engine…" phase.
- In-match render: 30–60 fps in the pane (fps counter, debug HUD);
  logic locked at 30.
- Known issue: with a hidden/occluded tab the RAF-driven logic crawls while
  audio keeps rendering (FramePacer vs throttled clocks) — resume is clean.

## Budgets (targets before publish)
- Bundle ≤ 35MB total; wasm ≤ 12MB (currently fine; watch texture growth —
  512px sheets add up. Consider DXT/basis later).
- DEPLOY → match ≤ 20s on a mid laptop: needs the synchronous init split
  into chunked frames (upstream boot re-entry work) or a worker; measure
  first with real marks.
- Steady 60 fps render / 30 logic on a mid laptop at 1024×768.

## Follow-ups
- performance.mark instrumentation in web/index.html (menu → fetch →
  wasm-instantiate → main() → first tick) reported to the debug log.
- Hashed asset filenames for immutable CDN caching (see docs/hosting.md).
- Investigate FramePacer under throttled clocks (background-tab crawl).

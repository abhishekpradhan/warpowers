# Web performance

Updated 2026-09-05. Measure the current candidate; older 1024×768 prototype
numbers do not certify the new widescreen build.

## Budgets and implementation

- Combined staged bundle: **≤64 MiB**. Content hashes deduplicate identical
  bytes and make engine, data, fonts and UI resources cacheable across visits.
- Desktop boot target: **≤20 seconds** on a midrange laptop over a real
  network. Local staging checks only the local portion of that requirement.
- Rendering choices: 1280×720 Performance, 1600×900 Balanced (default),
  1920×1080 High. Native UI is authored at 1280×720 and scales as a unit.
- Target steady 60 render / 30 logic updates per second, with usable input
  during large fights. Report rendered frames and logic separately.
- Keep ordinary hidden tabs paused. Diagnostic review/test sessions opt out
  so their explicit simulation continues while inspected in the background.

The art optimizer strips opaque alpha, uses lossless TGA RLE when it saves
space, and checks decoded pixels. Small atlases use explicit role-based size
contracts. Music remains the six attributed tracks; additional art should not
silently increase the loading budget.

## Current local evidence

- Candidate `6375e6bfb189`: **66,729,367 bytes (63.638 MiB)** staged,
  including the complete original roster, engine and notices. The packaging
  gate enforces the 64 MiB limit before replacing the previous working stage.
- Repaired bridge candidate reached the main loop in **542ms** on one local
  cached development-browser run (64 ms engine download/compile stage, 343 ms
  data stage, 136 ms initialization). This is not a cold-network result.
- Native supply/power and training checks ran through their required states;
  a dedicated crowded review scene now reports render timing, logic progress
  and WASM heap capacity. Heap capacity is not operating-system process RSS.
- A fresh recursive GitHub checkout also configures, builds and stages:
  `8b0a011a5989`, **66,729,527 bytes (63.638 MiB)**. This is build/size
  evidence; it does not add browser performance or gameplay measurements.

The currently staged `build.json` identifies each candidate and asset sizes.
Settings → Copy diagnostics includes the build ID, browser and measured boot
phases. `?review=stress&map=Maps/WPTest.map` selects the explicit stress fixture;
its output is a measurement, not an automatic declaration that a budget passed.

## Remaining release evidence

A 30–45-minute crowded run, a second/lower-end desktop, full Safari and Firefox
matches, and real-network first/repeat loading remain separate release checks.
A future protected hosting preview needs owner authorization. Verify actual
compression and cache behavior at that URL; do not infer wire size from the
uncompressed directory or assume a fixed compression ratio.

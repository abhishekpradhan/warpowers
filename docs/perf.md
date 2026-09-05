# Web performance

Updated 2026-09-05. Measurements below identify their candidate and test
conditions; local runs do not certify other browsers, hardware or networks.

## Budgets and implementation

- Combined staged bundle: **≤64 MiB**. Content hashes deduplicate identical
  bytes and make engine, data, fonts and UI resources cacheable across visits.
- Desktop boot target: **≤20 seconds** on a midrange laptop over a real
  network. Local staging checks only the local portion of that requirement.
- Rendering choices: 1280×720 Performance, 1600×900 Balanced (default),
  1920×1080 High. Native UI is authored at 1280×720 and scales as a unit.
- Target steady 60 render / 30 logic updates per second, with usable input
  during large fights. Report rendered frames and logic separately.
- Ordinary hidden tabs pause. Diagnostic review/test sessions opt out so
  their explicit simulation continues while inspected in the background.

The art optimizer strips opaque alpha, uses lossless TGA RLE where smaller
and checks decoded pixels. Explicit atlas contracts bound image sizes; solid
menu padding lies outside the sampled crop. Music retains the six attributed
tracks. The stager enforces the size limit before replacing a working stage.

## Current candidate and build evidence

- Candidate `66f4e32fcfab`: **66,740,374 bytes (63.649 MiB)** staged,
  including engine, data, UI and notices. This directory measurement was read
  from the current local stage; it is not compressed network transfer size.
- An earlier repaired bridge reached the main loop in **542 ms** on one local
  cached development-browser run (64 ms download/compile stage, 343 ms data,
  136 ms initialization). This is historical cached evidence, not a measured
  cold-network boot for the current candidate.
- A fresh recursive GitHub checkout configured, completed a 1,279-step clean
  build and staged `8b0a011a5989`, **66,729,527 bytes (63.638 MiB)**.
  That demonstrates build/size reproducibility, not browser performance or
  byte-identical compilation.
- The independent checkout then fetched the initial completed polish root `0ab5819`, engine
  `05c81c9908d95f6428b14a96935694539b6c1b9d` and DXVK `538cb703`. Tests,
  gates, incremental WASM build and staging pass with a clean tree and resolved
  recursive pins. Its candidate `a50ecbb361a0` is **66,734,559 bytes**,
  159 bytes above the earlier `2a5fb93551f9` stage and still below 64 MiB. This is an
  incremental rebuild of the earlier clean checkout, not another full clean build.

## Isolated crowded-battle measurement

The candidate whose ID begins `6b10`, with the steering correction, ran the
120-unit real attack-move fixture in isolation on an **M1 Max / 64 GB
MacBookPro18,2**, Chromium in-app browser, **Balanced 1600×900**. The fixture
reported 143 objects including its setup. No other game tab was active.

| Fixture observation | Render frames/s | Logic updates/s |
|---|---:|---:|
| 9.9 seconds | 59.9 | 30.5 |
| 19.9 seconds | 59.9 | 30.3 |
| 29.9 seconds | 59.9 | 30.2 |
| 40 seconds | 59.9 | 30.1 |
| 50 seconds | 59.9 | 30.1 |
| 60 seconds | 59.9 | 30.1 |

Reported WASM heap **capacity** stayed at **512 MiB**. This is the allocated
WASM memory buffer, not operating-system process RSS, live allocation usage
or evidence that the browser process consumes only 512 MiB. A battle was also
observed around the 11-minute mark; that was not a controlled soak test.

The one-minute isolated sample met the intended render/logic cadence under
these conditions. It does not establish long-run memory behavior, worst-case
late-game performance or performance on a lower-end computer.

`?review=stress&map=Maps/WPTest.map` selects the explicit fixture. Settings →
Copy diagnostics includes the build ID, browser and boot phases. Keep the
candidate, hardware, quality preset, concurrent tabs and observation duration
with every future measurement.

## Remaining release evidence

A controlled 30–45-minute crowded run with restart/redeploy, process-memory
measurements, a second/lower-end desktop, full Safari and Firefox matches,
and real-network first/repeat loading remain separate checks. A protected
hosting preview needs owner authorization. Verify compression and cache
behavior at that URL; do not infer wire size from the uncompressed directory
or assume a fixed compression ratio.

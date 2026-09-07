# Web performance

Budgets, the reasons behind them, and how to measure against them. Past
measurements are in
[history/2026-09-verification.md](history/2026-09-verification.md#performance-measurements-september-2026);
a local run never certifies other browsers, hardware or networks.

## Budgets

| Budget | Value | Why |
|---|---|---|
| Staged bundle | ≤ 64 MiB, enforced by `tools/genwebstage.py` before it replaces a working stage | Keeps a cold visit and every content update affordable on ordinary connections |
| Desktop boot | ≤ 20 seconds from navigation to the main menu on a midrange laptop over a real network | The web's advantage is zero friction; a long boot gives it away |
| Cadence | 60 rendered frames and 30 logic updates per second with usable input during large fights | The engine's logic rate is fixed at 30; rendering below 60 reads as stutter |
| Render presets | 1280×720 Performance, 1600×900 Balanced (default), 1920×1080 High; native UI authored at 1280×720 and scaled as a unit | One tested layout at three costs |
| Hidden tabs | Ordinary sessions pause; diagnostic sessions opt out | Auto-pause is the product behaviour and it should not look like a hang |

Implementation choices that serve these budgets: content-hashed immutable
asset URLs (engine, data, font and UI resources cache across visits and
identical bytes deduplicate), an art optimizer that strips opaque alpha and
uses lossless TGA RLE where smaller, explicit atlas contracts that bound image
sizes, and six music tracks re-encoded at 96 kbps.

## How to measure

### Bundle size

`python3 tools/genwebstage.py` prints the staged byte count and refuses to
stage above the limit. The number is the uncompressed directory size, not the
compressed transfer size; measure the wire size at the hosting URL, never by
assuming a compression ratio.

### Boot time

Settings → **Copy diagnostics** includes the build identifier, browser, and
the boot phases (engine download, data staging, engine initialization,
total). With `?debug=1` the page also logs a `[BOOT]` line. A cached local
boot is not a network boot: measure first and repeat visits at the real URL
and record the connection.

### Crowded battle

`?review=stress&map=Maps/WPTest.map` (or `WPTestJ` for the Jackal roster)
creates a bounded 120-unit attack-move encounter and reports rendered frames
per second, logic updates per second and WebAssembly heap capacity on screen.
It requires the **harness build** (`wasm-harness` preset) and `?debug=1`; see
[testing.md](testing.md). Run it in the only active game tab, in the
foreground, and keep the result for one minute or longer.

Record with every measurement: build identifier, hardware, operating system,
browser and version, quality preset, other open tabs, and observation
duration. The heap figure is the allocated WebAssembly memory buffer, not
operating-system process memory; read process memory from the browser's task
manager or the operating system.

### Long sessions

The controlled soak that the roadmap asks for is a 30–45 minute crowded match
with a restart and a redeploy, sampling process memory and frame timing every
few minutes. Frame pacing under a throttled or hidden tab is not a
measurement; keep the tab visible.

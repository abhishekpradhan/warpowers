# War Powers — publish checklist (Phase 5)

Nothing on this list authorizes a public deploy. Publishing remains gated on
an explicit user go (D013). Work through top to bottom; check items only with
evidence (a log line, a screenshot, a URL).

## 1. Product quality gate (D013 bar)
- [x] In-engine shell end-to-end: menu → deployment (battlefield + opposition
      + faction) → match → pause/restart/abandon → score → menu
- [x] Real opponent: AIPlayer with base building, economy, escalation tiers,
      difficulty, defense patrol / punish / eco-raid (Phase 4)
- [x] Music rotation, ambient beds, VO, SFX (user-confirmed audible)
- [ ] One full playthrough per difficulty by a human before go
- [ ] Second-machine sanity run (different Mac / lower-end hardware)

## 2. Performance budget
- [x] Local boot: 5.5s cold total (165ms engine dl, 214ms data, 5.2s init) —
      budget ≤20s
- [x] Frame budget on M-series: 60/s sustained through early-match combat
      (pump-rate measurement; see engine-notes Phase 5 entry)
- [ ] Frame rate through a BRUTAL late game (assault + air + punish + player
      army all fielded) — measure, don't assume
- [ ] Real-network boot numbers from a CDN deploy (see §5)
- Known perf debt (acceptable at current scale): money-readout font surface
  churn (W3DDisplayString rebuild) — revisit if late-game frames dip.

## 3. Browser matrix
- [x] Chromium (dev harness, daily driver)
- [x] Safari — BOOTS (beacon total=751ms, full asset stage + engine main
      loop reached); a human-played match remains a manual pre-go item
- [ ] Safari — one human-played match
- [ ] Firefox — not installed on this machine; boot beacon + match on a
      machine that has it (or install with user ok)
- Boot/fail beacons land in any static server's access log:
  `/wp-boot-ok?total=…&ua=…` on success, `/wp-boot-fail?…` on engine abort.

## 4. Branding / trademark surfaces
- [x] User-visible surfaces clean: tab/window title, page copy, all in-game
      strings (Generals.str audited — zero EA marks), score/menu screens
- [x] Attribution surfaces correct and REQUIRED: CREDITS.md, ASSETS.md,
      LICENSE-ASSETS.md (engine lineage GeneralsX/GPL, CC-BY music, etc.)
- [ ] Pre-go final sweep: `grep -riE "electronic arts|command & conquer|zero
      hour" webstage/` must return only attribution files
- Known + deliberate (devtools-visible only, not user-facing branding):
  engine binary name `GeneralsXZH.js/.wasm`, `Generals.str` filename
  (engine-hardcoded), `CNC_GENERALS_*` env names, GeneralsX console banner.
  These are engine-lineage identifiers; renaming is cosmetic and deferred.
- [ ] Formal trademark search + domain grab ("War Powers", e.g. warpowers.gg)
      before M1 public

## 5. Hosting (Vercel, per D013)
- [x] `vercel.json` + `.vercelignore` prepared: static serve of `webstage/`
      only, wasm content-type, 1h asset cache (NOT immutable — asset paths
      aren't content-hashed yet; bump genwebstage to hashed paths before
      switching to immutable), no-cache HTML/manifest
- [ ] PRIVATE preview deploy with Deployment Protection ON (user go required
      even for this — it sends content to a third-party host)
- [ ] Boot budget on the preview URL from a real network (beacon totals)
- [ ] Brotli/compression verified on .wasm and .js (Vercel default)
- [ ] Re-run browser matrix against the preview URL

## 6. Repos / licensing at go-time (D012)
- [ ] Create org; fork engine + dxvk publicly; push branches; transfer
      workspace; flip submodule URLs (plan in project memory / WORKSPACE.md)
- [ ] LICENSE / LICENSE-ASSETS.md / CREDITS.md land in the public repos
- [ ] README pass for the public workspace

## 7. After go
- [ ] LAN/relay multiplayer track (wasm-generals parity)
- [ ] Telemetry decision (even just beacon-level boot stats)

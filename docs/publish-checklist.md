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
- [x] Bundle size: 55MB staged (11MB wasm + ~44MB gamedata incl. music) —
      re-baselined ≤64MB (docs/perf.md); CDN brotli roughly halves wire
      size, verify on the preview deploy
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
      — deploy via `vercel` CLI from the local tree: `.vercelignore` uploads
      only `webstage/` + `vercel.json`, and NO GitHub↔Vercel integration is
      installed or needed (Vercel never gets repo access; nothing auto-deploys
      on push)
- [ ] Boot budget on the preview URL from a real network (beacon totals)
- [ ] Brotli/compression verified on .wasm and .js (Vercel default)
- [ ] Re-run browser matrix against the preview URL

## 6. Repos / licensing at go-time (D012)
Current organization (verified + normalized 2026-08-31; see D012 addendum):
- [x] Three private repos, all pushed and pinned: `warpowers` (workspace;
      dvijoke vendored inline per D020, submodule → engine),
      `warpowers-engine` (submodule → dxvk at `references/fbraz3-dxvk`),
      `warpowers-dxvk`. (`warpowers-dvijoke` archived read-only.) Every
      submodule URL points at OUR repo; every pinned SHA is reachable on
      its remote — `clone --recursive` reproduces the tree.
- [x] Remote scheme normalized in every checkout: `origin` = our private
      repo, fork parents/upstreams present fetch-only with push URL set
      to `DISABLED` (fbraz3/GeneralsX + TheSuperHackers + GeneralsXWeb on
      engine; doitsujin + fbraz3 on dxvk; OpenSAGE plugin ref). "Never
      push upstream" is now mechanically enforced.
- [x] GitHub Actions DISABLED at repo level on all four (inherited
      upstream CI burned private-repo minutes Aug 22–24: 9 runs on the
      engine mirror, 8 on dxvk; workflow files already stripped from our
      branches — the repo-level switch also covers future upstream-sync
      branches). Re-enable per-repo only if we ever add CI of our own.
- [ ] At go: create org; fork engine + dxvk publicly; push branches;
      transfer workspace (dvijoke ships inline in it, D020); flip
      submodule URLs (D012)
- [ ] LICENSE / LICENSE-ASSETS.md / CREDITS.md land in the public repos
- [ ] README pass for the public workspace: edit README.md in place —
      add the hosted Play URL, drop "(working title)" if the name is
      final, final tone once-over (README.draft.md was folded in and
      deleted 2026-08-31 per D011 — no parallel draft to maintain)

## 7. After go
- [ ] LAN/relay multiplayer track (wasm-generals parity)
- [ ] Telemetry decision (even just beacon-level boot stats)

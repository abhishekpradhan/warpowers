# Publish checklist (D012 execution plan)

Nothing here executes without the user's explicit go. This is the ordered
runbook for taking War Powers public.

## Phase 0 — final audits (private)
- [ ] Trademark sweep: grep every shipped surface (window title, page title,
      strings, README, repo names/descriptions) for EA marks. Engine GPL file
      headers keep their legal notices (lineage, not product surface).
- [ ] Asset audit: every file in `data/` has an ASSETS.md row; licenses are
      CC BY-SA 4.0 (ours), CC0/CC-BY (third party), or SIL OFL (font).
- [ ] Fresh-clone reproducibility on a second machine/user: clone --recursive,
      run every tools/ pipeline, build native + wasm, BASE_LOOP_OK.

## Phase 1 — GitHub org + true forks
- [ ] Create the org (name TBD with the user; check availability).
- [ ] Fork chain with real GitHub fork relationships (provenance visible):
      - engine: fork fbraz3/GeneralsX -> org/warpowers-engine; push
        `warpowers` + `warpowers-web` branches.
      - dvijoke: fork meerzulee/dvijoke -> org/dvijoke; apply
        tools/patches/dvijoke-d8web-atlas-probe-trace.patch as a commit.
      - dxvk: transfer/fork chain doitsujin/dxvk -> fbraz3/dxvk ->
        org/warpowers-dxvk (already exists as a plain repo; recreate as fork
        if provenance matters enough to rewrite).
- [ ] Workspace repo -> org/warpowers; update .gitmodules URLs; verify
      clone --recursive from the org.

## Phase 2 — public flip order
1. dxvk fork (leaf, no secrets)
2. dvijoke fork
3. engine fork
4. workspace repo (README.draft.md -> README.md, license files at root)

## Phase 3 — upstream PRs (goodwill + provenance)
- [ ] GeneralsXWeb: wasm audio fixes (zero-channel decode buffers; group
      routing bypass), INI unknown-block fatal diagnostics, drawable icon
      null-guards, missing-label once-only logging.
- [ ] Position each PR small and self-contained; reference our notes.

## Phase 4 — hosting (decision doc: docs/hosting.md)
- [ ] Execute the hosting decision (presumptive: Vercel, Deployment
      Protection ON until announce).
- [ ] Custom domain (D006 trademark/domain task) at announce time.

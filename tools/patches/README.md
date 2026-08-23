# Local patches to third-party checkouts

Patches we carry against dependencies that aren't our forks yet. Each one is
the committed source of truth for a change that otherwise lives only in a
gitignored working tree — re-apply after a fresh clone.

| Patch | Target | Apply | Disposition |
|---|---|---|---|
| dvijoke-d8web-atlas-probe-trace.patch | `dvijoke/` checkout (github.com/meerzulee/dvijoke, MIT) | `git -C dvijoke apply ../tools/patches/dvijoke-d8web-atlas-probe-trace.patch` | Lands in our dvijoke fork at publish time (decisions.md D012) |

# Credits

War Powers is built on the shoulders of open work. Everything listed here is
used within its license terms; the full per-file ledger lives in ASSETS.md.

## Engine
- **GeneralsX** (GPL-3.0 with EA's additional terms, from EA's source
  release) — the community source port this project forks.
- **DXVK** (zlib) — D3D→Vulkan layer used by the native macOS development
  build only (not part of the web build).
- **dvijoke** (MIT) — D3D8→WebGL2 translation layer for the browser build.
  Vendored inline at `dvijoke/` (upstream meerzulee/dvijoke; our copy is
  upstream +3 commits, subtree-merged from warpowers-dvijoke @ ba6791de);
  carries its own LICENSE.

## Art
- **Quaternius** — quaternius.com, CC0. CC0 source packs used during prototyping; retained in the repository
  as historical reference. The four former runtime adaptations have been
  replaced by project-authored models. We retain this acknowledgement of
  the work that helped establish the prototype.

## Fonts
- **Liberation Sans** — Red Hat / liberationfonts, SIL OFL 1.1.

## Tools
- **OpenSAGE.BlenderPlugin** — W3D export for Blender.
- **Blender** — all War Powers models and textures are produced through
  scripted, reproducible Blender pipelines (tools/blender/).

## Music

Music by Kevin MacLeod (incompetech.com):
"Volatile Reaction", "Interloper", "Crypto", "Rites", "Mechanolith", "Stormfront"
Licensed under Creative Commons: By Attribution 4.0 License
https://creativecommons.org/licenses/by/4.0/

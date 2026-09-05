# Credits

War Powers uses work from the projects and creators below. Content provenance
is recorded in ASSETS.md; browser dependency licenses and their complete notices
are indexed in [licenses/third-party.json](licenses/third-party.json).

## Engine
- **GeneralsX** (GPL-3.0 with EA's additional terms, from EA's source
  release) — the community source port this project forks.
- **DXVK** (zlib) — D3D→Vulkan renderer used by the native macOS development
  build. The browser uses Wine-derived DirectX headers fetched with DXVK
  (LGPL-2.1-or-later), recorded in the dependency inventory.
- **dvijoke** (MIT) — D3D8→WebGL2 translation layer for the browser build.
  Vendored inline at `dvijoke/` (upstream meerzulee/dvijoke; our copy is
  upstream +3 commits, subtree-merged from warpowers-dvijoke @ ba6791de);
  carries its own LICENSE.
- **FreeType 2.14.3** (FreeType License, FTL) — browser font rendering.
  Portions of this software are copyright © 1996–2026 The FreeType Project
  (https://freetype.org). All rights reserved. This software is based in part
  on the work of the FreeType Team.

## Historical layout
- **Felipe Keller Braz / GeneralsX** — the GPL `ExtrasMenu.wnd` was copied
  into the prototype on 2026-08-21 and removed from the unreleased root dataset
  on 2026-09-05. Its earlier description as original CC BY content was incorrect;
  historical copies retain GPL terms. ASSETS.md records the upstream commits.

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

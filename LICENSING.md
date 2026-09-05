# War Powers — Licensing

Root code is MIT, project-authored game content is CC BY 4.0, and imported
files retain their own licenses. The compiled browser engine is distributed
under GPL-3.0 with EA's additional terms and the applicable dependency notices.

[ASSETS.md](ASSETS.md) records content provenance and per-file licenses;
[CREDITS.md](CREDITS.md) carries acknowledgements. The browser code dependency
inventory and notice files are linked from [licenses/third-party.json](licenses/third-party.json).
Policy decisions D019 and D022 are recorded in [docs/decisions.md](docs/decisions.md).

## Our code — MIT

Code, tooling and documentation authored in the root repository — including
`tools/`, `web/`, build/generator scripts and `docs/` — are MIT licensed
(see [LICENSE](LICENSE)). Imported code keeps its upstream license.

## Our content — CC BY 4.0

Original War Powers models, textures, audio, maps, UI layouts, strings and
INI data are licensed under **Creative Commons Attribution 4.0 International**,
subject to the per-file exceptions and historical records in ASSETS.md.

- [Full CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/legalcode)
- Attribute project-authored content to "War Powers project" and link to the
  project's published source location.

## Imported content

The pre-approved inbound content licenses are CC0/public domain, CC BY and
SIL OFL. Their conditions differ: CC BY requires attribution and modification
notices; OFL fonts must retain OFL and the copyright notice, cannot be sold
alone, and must respect reserved font names when modified. CC0 source material
retains its dedication; our original additions to CC0 adaptations use CC BY 4.0.

ShareAlike, GPL-licensed art and NC imports require a fresh decision-log entry
before import. Retail EA assets or extracted game data, unlicensed assets, and
ND imports that cannot be adapted and shared through our pipeline are excluded.

| Import | License | Notes |
|---|---|---|
| Six music tracks by Kevin MacLeod (incompetech.com) | CC BY 4.0 | Re-encoded/trimmed for the browser; track credits and changes in ASSETS.md and CREDITS.md |
| Quaternius models in `refs/quaternius-tanks/` | CC0 1.0 | Historical prototype references; current production models are project-authored replacements and these references are not staged |
| Liberation Sans in `data/Fonts/` | SIL OFL 1.1 | Copyright and license at `data/Fonts/LICENSE-LiberationFonts` |

The former `data/Window/Menus/ExtrasMenu.wnd` was copied verbatim from the GPL
engine repository, not merely authored using the same format. It was incorrectly
included in the original-content declaration. The unused root copy was removed
from the unreleased dataset on 2026-09-05; ASSETS.md preserves its provenance.
Historical copies remain GPL licensed. The engine repository retains its own copy.

## Code from other projects

- `engine/`, our GeneralsX fork: GPL-3.0 with EA's additional terms from the
  Generals source release. The full terms are in `engine/LICENSE.md`.
- `dvijoke/`, vendored from meerzulee/dvijoke: MIT. Its D3D8-to-WebGL2 renderer
  is compiled into the browser engine; `dvijoke/LICENSE` preserves the notice.
- FreeType 2.14.3: the browser build selects the FreeType License (FTL).
  Portions of this software are copyright © 1996–2026 The FreeType Project
  (https://freetype.org). All rights reserved. This software is based in part
  on the work of the FreeType Team.
- The native DXVK renderer uses zlib terms and is not used by the browser.
  Wine-derived DirectX headers fetched with DXVK are used by the browser build
  under LGPL-2.1-or-later; their notices are included in the dependency inventory.
- Emscripten and the remaining browser dependencies retain the licenses and
  notices recorded in [licenses/third-party.json](licenses/third-party.json).

The combined `GeneralsXZH.wasm/.js` engine is GPL-3.0 with EA's additional
terms. Compatible dependency licenses and notices still apply to their
respective code. Separately authored game data retains its per-file license;
copying or adapting upstream content must be reviewed on its own provenance.
Repository or file-format boundaries alone do not establish a license exception.

## Source for a public browser release

The project is unreleased. The owner plans to deploy manually to Vercel and
publish the Git repositories afterward. The corresponding source must be
accessible to recipients **from the first public playable deployment**. If the
repositories are still private, publish a complete immutable source archive
first and link it from the game's credits. Making the repositories public
before the playable deployment is another option.

The source package must cover the distributed engine, vendored renderer,
required dependency source and build scripts/instructions. Record the exact
commits or release tag, dependency revisions, toolchain versions and the
resulting JavaScript/WASM hashes. Include the required notices and review
archive contents; do not copy a local `_deps` tree wholesale, which may contain
optional proprietary SDK material or unrelated build artifacts.

Stage a public release with `python3 tools/genwebstage.py --release --source-url`
followed by the actual HTTPS source archive or release page URL. The stager
records that URL, engine artifact hashes and the dependency-notice link in
`source.json`. This records the supplied location; it does not prove that the
archive matches the binary or is complete.

Before release, validate a clean rebuild from the source package and download
the source and notices without signing in. Preserve the source for every
distributed build. The remaining checks are in
[docs/publish-checklist.md](docs/publish-checklist.md).

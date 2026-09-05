# Browser dependency notices

`third-party.json` records the dependency versions inspected in the existing
WebAssembly build on 2026-09-05. Each `notice` path is relative to this directory.
The release stager must copy the manifest and every referenced notice together.
These notices supplement the engine, renderer, project and game-data licenses;
they do not replace the GPL corresponding-source requirements.

The license text comes from the actual fetched dependencies in
`engine/build/wasm/_deps/` and the Emscripten 6.0.8 SDK used by that build.
The SDK revision is `e5bd3d0874e302a18f13c5b41f5bacf9a40c8e59`.
Upstream source locations and the selected license alternatives are recorded in
the manifest. Where a dependency has multiple license choices, retaining its
complete upstream license file does not change the choice recorded there.

The inventory includes notices for linked libraries, inline header code and
runtime support. It conservatively retains bundled portable source notices even
when a particular function may be removed by the linker. It excludes optional
GameSpy console SDK/sample sources, native DXVK shared libraries, Miles, Bink,
OpenAL, FFmpeg and 3DS Max SDKs, which are not part of this browser build.

Specific source records:

- GameSpy: `LICENSE` and the notice in `src/common/md5c.c`.
- GLM: the MIT alternative in `copying.txt`; GLI: the MIT alternative in
  `manual.md`.
- Emscripten: complete root `LICENSE`, including its Node-derived path code.
- musl: complete `COPYRIGHT`, plus verbatim copyright and permission comment
  blocks from the portable math, complex, regex, crypt and standard-library
  sources. Each block identifies its upstream file paths.
- FreeType: complete `docs/FTL.TXT`, with the required product credit and the
  separate notices from the BDF/PCF drivers, hash implementation and
  HarfBuzz-derived source headers.
- LLVM compiler-rt, libc++, libc++abi and libunwind: each component's complete
  `LICENSE.TXT` as bundled by Emscripten.
- SDL3: `LICENSE.txt`, bundled yuv2rgb/HIDAPI licenses, and separate notices in
  the portable math and standard-library code.
- zlib: the Emscripten port's `LICENSE`; LZH-Light: the notice in `lzhl.h`.
- miniaudio: the license at the end of the actual `miniaudio.h`; stb: the MIT
  alternative in `LICENSE`.
- DXVK: version 2.6 project license, the native DirectX header README and header
  notices, plus the complete LGPL 2.1 text obtained from
  <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt>. The project license was
  checked against the local upstream `v2.6` Git tag.

Before releasing a different engine build, compare its fetched dependencies and
SDK version with this inventory and update the notices when needed. In
particular, the current engine build fetches miniaudio from `master`; its audited
header version and SHA-256 are recorded in the manifest. This static inventory
does not pin that download or prove the provenance of a future build. Do not
copy an entire dependency cache into a source release without checking optional
third-party content and preserving the applicable source notices.

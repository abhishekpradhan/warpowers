# Releasing War Powers

How a public build is produced, published and kept reproducible. A release is
two things that must appear together: a staged `webstage/` bundle on static
hosting, and the complete corresponding source for exactly that bundle,
reachable from the game's credits page without signing in. The compiled engine
is GPL-3.0, so the second is an obligation, not a courtesy.

This page is process only. Whether a candidate is *ready* — human playtests,
browser matrix, balance — is tracked in [docs/roadmap.md](docs/roadmap.md).

## 1. Before you start

- The gate list in [CONTRIBUTING.md](CONTRIBUTING.md#tests-and-gates) is
  green on the exact commits you will ship.
- `ASSETS.md`, `CREDITS.md`, `LICENSING.md` and `licenses/third-party.json`
  describe the content and dependencies of *this* build. Compare the engine's
  fetched dependencies (`engine/build/wasm/_deps/`) and the Emscripten
  revision with the inventory; update the notices when they differ
  ([licenses/README.md](licenses/README.md) explains what is recorded and
  why miniaudio needs a look every time).
- `CHANGELOG.md` has a release section for the version.
- The credits page (`web/credits.html`, the footer) and the README carry the
  EA non-affiliation sentence; `index.html` has none and needs none. No
  user-visible surface carries EA marks (decision D006 covers the name).

## 2. Pin the inputs

Record, in the release notes and next to the archive:

- root commit or tag, engine commit, DXVK commit, and the dvijoke subtree
  revision noted in `CREDITS.md`;
- the dependency versions and revisions from `licenses/third-party.json`;
- the toolchain: Emscripten version and SDK revision, CMake, Ninja, Python;
- the build commands (the README recipe, from a clean `engine/build/wasm`).

Build with the `wasm` preset only. Never ship a `wasm-harness` build.

## 3. Prepare the corresponding source

The package must let a recipient rebuild the shipped engine: the root
repository (including `dvijoke/`), the engine repository at the pinned commit,
every dependency source the engine's CMake fetches, the build scripts and
instructions, and all license notices. Inspect the package rather than
copying a local `_deps` tree wholesale — dependency caches can contain
optional proprietary SDK material or unrelated build artifacts.

Make it immutable: a tagged release with an attached archive is the simplest
form. Then prove it: rebuild from the package with the recorded toolchain on
a clean machine or container, and download it signed out.

## 4. Stage the candidate

```sh
python3 tools/genwebstage.py --release --source-url https://<host>/<path-to-source-archive-or-release>
```

`--release` requires the source URL and runs the content gates; the stager
refuses a candidate above 64 MiB and never deploys. Then verify in
`webstage/`:

- `build.json` — the build identifier; note it with the release.
- `source.json` — `status: provided`, the exact URL, and the SHA-256 and size
  of `GeneralsXZH.js` and `GeneralsXZH.wasm`. Record those hashes.
- `credits.html` — the "Corresponding source for this build" link, the
  repository links, and every notice link under `licenses/` resolves.
- `licenses/third-party.json` and its notice files are present.

The stager records the URL you supplied; it does not prove the archive
matches the binary. Step 3 does.

## 5. Deploy and verify at the URL

Deploy only the `webstage/` directory (`.vercelignore` and `vercel.json` are
set up for that); nothing deploys on push. At the public URL check:

- `GeneralsXZH.wasm` is served as `application/wasm`, JavaScript as
  `text/javascript`, both compressed;
- `/assets/*`, `app.*`, `core.*` and `styles.*` are cached immutably;
  `index.html`, `build.json`, `source.json` and `credits.html` revalidate;
- the credits page, the source link and the notices open signed out;
- the build identifier in Settings → Copy diagnostics matches `build.json`.

Browser matrix at the deployed URL, on at least two machines: current Chrome,
Edge, Firefox and Safari — boot, a full match, a checkpoint save and resume,
fullscreen. Measure first and repeat visits over a real network against the
20-second boot budget ([docs/perf.md](docs/perf.md)).

## 6. Keep it

Preserve the source package, the notices and the recorded hashes for every
build that was ever public, including builds superseded by a later deployment.
Tag the root, engine and DXVK repositories with the same release name.

## When the repositories move

The first release publishes under the personal account (D026), so nothing in
this section applies to it. The project's Git URLs (`github.com/abhishekpradhan/…`)
are written into the files below. Update all of them only if the repositories
later transfer to another account or organization, then rebuild and restage so the credits page and the
submodule pointers agree. Confirm the list with
`git grep -l "github.com/abhishekpradhan"` in each repository before editing.

Root repository:

1. `.gitmodules` — engine submodule URL
2. `README.md` — the clone command
3. `web/credits.html` — the three repository links on the credits page
4. `dvijoke/README.md` — the vendored-copy banner
5. `.github/ISSUE_TEMPLATE/config.yml` — the contributing-guide and security contact links

Engine repository (`engine/`):

6. `.gitmodules` — DXVK submodule URL
7. `README.md`, `CONTRIBUTING.md`, `SECURITY.md` — project and guide links
8. `cmake/dx8.cmake` and `cmake/wasm-deps.cmake` — fork source URLs used when the local checkouts are absent
9. `.github/ISSUE_TEMPLATE/*` and `.github/instructions/*` — template contact links

DXVK repository (`engine/references/fbraz3-dxvk`): `README.md` and
`CONTRIBUTING.md` — project and engine links.

Existing clones keep working after `git submodule sync --recursive`.

## Launch URL

The playable URL is `https://warpowers.vercel.app` until a purchased domain
replaces it (D026). When a domain arrives, add it to the Vercel project, keep the
`vercel.app` address as a redirect, and update the README play link; nothing in
the game bundle embeds the hostname.

## Hosting before the public release

The Vercel Hobby plan cannot put Vercel Authentication on production
deployments, and a project's first deployment is promoted to production
automatically. Keep the production slot occupied by a blank placeholder page
(no game files, `noindex`) so that `warpowers.vercel.app` reveals nothing, and
deploy the game only as preview deployments, which Standard Protection guards
behind a Vercel login. Never run `vercel deploy --prod` with the game until the
public release. The placeholder lives outside the repository; any static page
with a `vercel.json` sending `X-Robots-Tag: noindex, nofollow` will do.

## GitHub repository settings

`.github/workflows/ci.yml` (the gate list on every push and pull request) and
`.github/workflows/wasm-build.yml` (an on-demand and weekly engine build that
uploads `webstage/` as an artifact) are committed, but **Actions are disabled
at the repository level** on the root, engine and DXVK repositories. Enable
them in each repository's settings as part of the public release. The engine
repository carries its own `.github/workflows/qa.yml`; the DXVK repository
carries no workflows on the project branch.

In the same pass, enable **private vulnerability reporting** (Settings →
Code security) on the root, engine and DXVK repositories. `SECURITY.md`,
`engine/SECURITY.md`, `CODE_OF_CONDUCT.md` and both
`ISSUE_TEMPLATE/config.yml` files send reporters to that form, so a
repository without it has a security policy that leads nowhere.

## History

Git history is not rewritten when files are removed from the tree. In
particular, an early prototype copied a GPL layout file from the engine
repository into the dataset (recorded in `ASSETS.md`); historical copies keep
their GPL terms, and past root content must not be described as entirely
original CC BY work.

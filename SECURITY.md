# Security policy

War Powers is a pre-release browser game with no accounts, no server-side
state and no telemetry. Even so, it runs a large C++ engine compiled to
WebAssembly, serves content from static hosting and stores checkpoints in the
player's browser, so there are things worth reporting.

## Reporting a vulnerability

Please use GitHub's **private vulnerability reporting**: open the repository's
**Security** tab and choose *Report a vulnerability*. Reports reach the
maintainers only. Do not open a public issue for anything exploitable, and do
not send reports to personal addresses.

Include what you can: the build identifier from Settings → Copy diagnostics,
browser and operating system, a minimal reproduction, and what you believe
the impact is. You will get an acknowledgement within seven days and a
follow-up once the report has been triaged; there is no fixed disclosure
window yet, but we will agree one with you rather than leave a report open.

There is no bug bounty. Credit in the changelog and release notes is offered
to anyone who wants it.

## Scope

In scope:

- the web shell and its persistence code (`web/`), including how it handles
  URL parameters, browser storage, operation-record backups and engine
  callbacks;
- the tools that generate, validate, stage and serve the game (`tools/`),
  in particular anything that could make the stager or the local server
  read or write outside their intended directories;
- the engine fork in `engine/` as compiled for the browser, including the
  vendored renderer in `dvijoke/`, where crafted data files (maps, INI, W3D,
  TGA, audio, saves) reach engine parsers.

Out of scope:

- issues that only exist in upstream GeneralsX or the original engine source
  and cannot be reached through the War Powers dataset in the browser build —
  please report those upstream;
- the native macOS development build, which is a developer tool and never
  ships;
- denial of service against a player's own browser tab by supplying it
  crafted local data, unless it also crosses an origin or storage boundary;
- vulnerabilities in third-party hosting or CDN infrastructure.

## Supported versions

Only the `main` branch and the most recent hosted build receive fixes. There
are no maintained release lines yet.

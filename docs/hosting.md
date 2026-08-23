# Hosting decision (prepared; no deploy until go)

The web build is a fully static bundle: `webstage/` = engine js+wasm (~11MB)
+ gamedata (~19MB total staged) + one HTML page. No server-side logic today.

## Recommendation: Vercel (static) — matches D013's presumption

| Criterion | Vercel | Railway | Modal | Cloudflare Pages |
|---|---|---|---|---|
| Static + CDN + brotli | ✅ first-class | ⚠️ runs a server for static | ❌ compute-oriented | ✅ first-class |
| Private iteration before launch | ✅ Deployment Protection | ⚠️ manual auth layer | ⚠️ manual | ✅ Access policies |
| Per-commit previews | ✅ | ✅ | ❌ | ✅ |
| Large-asset caching (11MB wasm) | ✅ immutable asset caching | ✅ | n/a | ✅ (100MB/file limit fine) |
| Future WebRTC lobby (multiplayer) | ❌ (needs a server) | ✅ natural fit | ⚠️ possible | ⚠️ Workers/DO possible |
| Account already exists | ✅ | ✅ | ✅ | ❌ |

Plan: Vercel for the game bundle now; **Railway reserved** for the future
multiplayer lobby/relay service (the merged web branch already carries a
WebRTC transport expecting one); Modal stays for potential asset-pipeline
compute (batch bakes), not hosting.

Deploy mechanics when approved: `vercel deploy webstage/` (or a repo-linked
project building via `tools/genwebstage.py`), Deployment Protection ON,
custom domain at announce. Cache headers: engine js/wasm + gamedata are
content-hashed by the page's `?v=` buster today; move to hashed filenames
before launch so CDN caching is immutable-clean.

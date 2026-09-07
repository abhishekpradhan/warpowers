<!-- Keep the pull request focused on one player-visible outcome or one engineering change. -->

## Trigger

<!-- What was wrong, missing or confusing? Link the issue if there is one. -->

## Changed behaviour

<!-- What does a player, contributor or the build do differently now? Name the faction, unit, mission, tool or document involved. -->

## Checks performed

<!-- Tick what you ran; say what remains unverified. The gate list is in CONTRIBUTING.md. -->

- [ ] `node --test tests/*.test.mjs`
- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'`
- [ ] `python3 tools/check_content.py` / `validate_gameplay.py` / `lint_voices.py`
- [ ] Engine and renderer fixtures (`engine/scripts/qa/test-*.py`, `dvijoke/d8web/tests/test_resources.py`) when engine or renderer code changed
- [ ] Restaged and played the change in a browser (which browser, which mission/faction/difficulty):
- [ ] Diagnostic modes used, and what they inject or force:

## Provenance (for any new or changed asset)

<!-- Every asset family needs an ASSETS.md row and a regenerated registry. Delete this section if no asset changed. -->

- [ ] `ASSETS.md` row added or updated (source, author, license, date)
- [ ] `python3 tools/check_content.py --write-registry` run and `data/asset-registry.json` committed
- [ ] Generator edited alongside its generated output; nothing hand-edited
- [ ] No retail-derived content, in any form

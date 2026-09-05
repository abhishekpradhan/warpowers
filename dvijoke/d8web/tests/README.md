# Resource contract tests

Run `python3 dvijoke/d8web/tests/test_resources.py` from the project root, or
`python3 tests/test_resources.py` from this package. Requires Python 3 and a native
C++20 compiler with AddressSanitizer and UndefinedBehaviorSanitizer; set `CXX` to
select a compiler.

The runner compiles the actual frontend with a CPU-only backend and deletes its
temporary binary afterward. No browser, GPU context, game assets, or downloaded
dependencies are needed.

The contracts cover valid surface copies, rejected rectangle bounds (including
an invalid later rectangle leaving the destination untouched), and mip-level
surface ownership in different release orders. Backend texture counters verify
that a retained surface keeps storage alive and that the final release destroys
the texture, including after repeated level queries. Sanitizers fail the run on
invalid memory access or undefined behavior.

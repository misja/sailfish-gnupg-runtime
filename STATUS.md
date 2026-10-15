# Current source status

Experimental source snapshot. General release acceptance remains open.
Repository issues track open work; pull requests record proposed changes and checks.
See docs/EXPORT_SCOPE.md for build prerequisites and known support limits.

Session handoff, 2026-10-15: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3)
owns lifecycle work. PR #12 is approved and merged. The next
[trusted-state slice](docs/lifecycle-trusted-state-20261015.md) adds cold bootstrap,
whole-payload generation checks and explicit same-generation recovery with an
early loader lock. Candidate 0.5 adds system flock; Python 3 remains required.
All 77 host and 72 selected SDK tests passed. An inert RPM probe verified manifest
formation after payload postprocessing; the full GnuPG RPM was not rebuilt.
No real root state, package installation or device change occurred. Changed-
payload transactions, legacy migration and independent verification remain open.
Live issue/PR state is authoritative; this is not a ready device upgrade.

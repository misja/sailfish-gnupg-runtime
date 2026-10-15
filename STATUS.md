# Current source status

Experimental source snapshot. General release acceptance remains open.
Repository issues track open work; pull requests record proposed changes and checks.
See docs/EXPORT_SCOPE.md for build prerequisites and known support limits.

Session handoff, 2026-10-15: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3)
owns lifecycle work. The maintainer approved the [contract basis](docs/lifecycle-contract.md)
and PR #10 is merged. The next [implementation slice](docs/lifecycle-implementation-20261015.md)
adds a separate direct-IPC supervisor and an experimental admission primitive.
All 39 host tests and 34 selected SDK tests passed; direct-helper cleanup after
wrapper TERM/KILL was measured in both environments. Admission is not yet wired
into wrappers/RPM hooks. Agent/descendant quiescence, changed-payload integration
and verification separate from implementation remain open. No package/device
installation or release acceptance is implied. Live issue/PR state is authoritative.

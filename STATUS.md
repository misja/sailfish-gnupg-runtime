# Current source status

Experimental source snapshot. General release acceptance remains open.
Repository issues track open work; pull requests record proposed changes and checks.
See docs/EXPORT_SCOPE.md for build prerequisites and known support limits.

Session handoff, 2026-10-15: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3)
owns lifecycle work. The [proposed contract](docs/lifecycle-contract.md) defines
admission, drain, interruption and package maintenance requirements. Host policy
regressions pass, but the existing observer reproduces IPC survival after wrapper
TERM/KILL; [baseline evidence](docs/lifecycle-baseline-20261015.md) records limits.
Shared admission, changed-payload integration and independent verification remain
open. No runtime/RPM behavior, package installation or release claim changed.

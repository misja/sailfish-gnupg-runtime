# Current source status

Experimental source snapshot. General release acceptance remains open.
Repository issues track open work; pull requests record proposed changes and checks.
See docs/EXPORT_SCOPE.md for build prerequisites and known support limits.

Session handoff, 2026-10-15: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3)
owns lifecycle work. PRs #10 and #11 are approved and merged. The next
[wrapper/agent integration](docs/lifecycle-wrapper-integration-20261015.md)
connects both entry points to mandatory admission and separate persistent-agent
registration. All 55 host and 50 selected SDK tests passed; the actual RPM install
fragment staged seven exact files/modes. Candidate 0.4 adds Python 3 as a runtime
dependency. No full RPM build or installation ran. Trusted root state bootstrap,
payload-generation authentication, maintenance recovery, changed-payload tests
and independent verification remain open; this is not a device-ready upgrade.
Live issue/PR state is authoritative.

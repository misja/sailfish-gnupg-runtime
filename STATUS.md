# Current source status

Experimental source snapshot. General release acceptance remains open.
Repository issues track open work; pull requests record proposed changes and checks.
See docs/EXPORT_SCOPE.md for build prerequisites and known support limits.

Session handoff, 2026-10-15: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3)
owns lifecycle work. PR #12 is merged; PR #13 remains draft for human review.
The [transition-state continuation](docs/lifecycle-transition-state-20261015.md)
builds on #13 and records original/destination generations atomically, with
explicit destination or restored-original reconciliation. It adds no CLI action
or package writer. Package-writer supervision, removal, legacy migration and
independent verification remain open. Test evidence is linked from that record.
No real root state, package installation or device change occurred.
Live issue/PR state is authoritative; this is not a ready device upgrade.

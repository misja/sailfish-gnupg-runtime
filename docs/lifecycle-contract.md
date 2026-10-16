# Private runtime maintenance policy

Experimental source; automatic upgrade/removal is unsupported.
Owner: Misja Hoebe. Tracking: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).
This replaces the proposed custom lifecycle coordinator contract after scope review.

This policy concerns the separate `sailfish-gnupg-private` package and processes
using its files under `/usr/libexec/sailfish-gnupg`. Jolla’s GnuPG remains
installed and is outside this maintenance operation. Running clients (including
pass/OTP operations) and private agents can retain old executables/libraries
while package files are replaced. That is why process coordination is needed;
separate package paths do not make live replacement safe automatically.

The shell entry points use an explicit private home, private executables/libraries,
strict agent identity checks and bounded IPC. They do not implement global
admission, process ownership across a complete GnuPG operation or package locking.
GnuPG can start its configured private agent. A per-home stop does not establish
that all runtime users and helpers have stopped.

For a separately authorized manual SDK experiment, the operator must prevent all
users and callers from starting this runtime, finish outstanding work and stop
positively identified private agents for the known synthetic homes before payload
replacement/removal. If exclusion or process shutdown cannot be established, do
not change the installed payload. There is no enforced general upgrade path yet.

Never stop stock Jolla or unrelated user processes; do not use killall, name-based
pkill, global gpgconf cleanup, secret-bearing home discovery or home deletion.
A missing socket does not establish process absence. Preserve all user data.
Interrupted package changes require inspection/repair before use, not automatic
reopening or a promise of custom rollback.

Release integration must demonstrate start exclusion during replacement/removal
and safe handling of existing private agents with synthetic fixtures. Old RPM
%preun alone is too late for an upgrade: the new payload is already installed
([RPM ordering](https://rpm.org/docs/4.20.x/manual/triggers.html)). SDK-specific
integration and independent security/release verification remain open.

The removed Python admission, watcher, generation and recovery framework remains
available in Git history (PRs #11–#14); it is not a runtime dependency or a future
implementation requirement. Retained IPC interruption evidence is documented in
[lifecycle implementation](lifecycle-implementation-20261015.md).

# Private runtime maintenance policy

Experimental source; automatic upgrade/removal is unsupported.
Owner: Misja Hoebe. Tracking: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).
This replaces the proposed custom lifecycle coordinator contract after scope review.

The shell entry points use an explicit private home, private executables/libraries,
strict agent identity checks and bounded IPC. They do not implement global
admission, process ownership across a complete GnuPG operation or package locking.
GnuPG can start its configured private agent. A per-home stop does not establish
that all runtime users and helpers have stopped.

## Proposed experimental maintenance boundary

Proposal for maintainer review, not a tested procedure or device support claim.
Use a dedicated disposable execution environment and replace the entire instance
between experiments. Do not upgrade/remove the runtime in a live instance or
perform offline RPM surgery. This deliberately limits development scope; normal
package-manager upgrade/removal remains an unresolved part of issue #3.

1. Identify the old instance A and candidate B, their reviewed source/package
   identities, and the environment manager that owns all their execution. Confirm
   that installed private payloads and writable roots are not shared with the
   host, SDK, another instance or real user homes. Do not share or forward agent
   sockets between instances, the host or other environments. A build directory is not
   an isolated execution environment. Docker is not sufficient evidence merely
   because sfdk uses it; an additional LXC layer is not required.
2. Prepare candidate B separately using existing build tools. Do not connect real
   homes, credentials or stores. A fresh full SDK build of candidate 0.6 is still
   required; previous build evidence does not cover it.
3. Finish synthetic operations in A and request stop of its positively identified
   private agent under its owning user. Then stop the entire disposable instance
   through its manager, disabling automatic restarts and alternate launch paths.
4. Establish that all processes belonging to A, including helpers and surviving
   descendants, have exited and cannot restart. A socket absence, shell exit,
   per-home stop or one process scan alone is insufficient. If ownership,
   separation or shutdown is uncertain, do not activate B or retire A's payload.
5. Activate B with a new named synthetic home only after that exclusion is
   established. Check its reviewed package identity and synthetic behavior.
   Retirement/removal is of the explicitly identified stopped disposable instance,
   not an in-place RPM removal test. Preserve fixture homes/evidence outside the
   disposal boundary as copies, not shared runtime homes; do not delete user data
   or unrelated SDK/stock files.

If shutdown times out, retain A unchanged and do not proceed. If preparation or
activation fails, leave B unused and inspect/repair or recreate it explicitly;
do not automatically restart either instance. An interrupted switch is not
accepted until the manager establishes which instance/processes exist. There is
no rollback guarantee or new persistent recovery state.

## Minimal acceptance plan

Before any installation/destructive experiment, review the exact environment,
commands, affected paths, restart controls and allowed interruption point with
Misja. None is authorized by this document. Record only bounded public/synthetic
metadata: source/artifact identities, manager state, process identities, results
and declared stock-file sentinels; no home discovery or secret-bearing dumps.

Check (a) isolation of installed payloads, (b) old-instance shutdown including a
synthetic surviving helper and attempted restart, (c) no B activation after
shutdown uncertainty, (d) candidate identity/behavior and unchanged unrelated
stock sentinels, and (e) retained fixture data after retirement. Interruption at
a reviewed switch point must leave no ambiguous instance eligible for use.
A separate reviewer assesses the evidence before maintainer acceptance.

No suitable disposable topology or shutdown/activation checks have yet been
verified. This proposal therefore does not close issue #3. Live RPM replacement,
in-place removal, target/device behavior and independent release verification
remain open; accepting cold development replacement must not mark those passed.

## Alternatives and maintenance cost

Per-home stopping alone misses other callers. Wrapper locking alone misses direct
binaries and persistent agents. A new custom coordinator would reintroduce the
removed maintenance burden before a release requirement justifies it. Whole-
instance replacement delegates lifecycle ownership to an existing environment
manager, at the cost of a fresh disposable candidate and explicit isolation checks.
Repeat relevant checks for an adopted payload/SDK/target change, not for every
remote upstream commit. This does not require a new runtime dependency or service.

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

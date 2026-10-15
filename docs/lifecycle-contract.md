# Private runtime lifecycle contract

Status: proposed v1, 2026-10-15. Owner: sailfish-gnupg-runtime;
maintainer decision: Misja Hoebe. Tracking: [runtime issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).
This defines required behavior for implementation and review. The present
wrappers and RPM do not implement the complete contract. It grants no package
installation, device-test or release permission.

## Scope and invariants

The supported entry points are `sailfish-gpg` and `sailfish-gpg-agent`.
GnuPG helpers and their descendants belong to the admitted operation. The
persistent agent belongs to its explicit private home and user, rather than to
the lifetime of one client. The runtime repository owns this protocol; pass/OTP
must use it rather than add a competing cleanup or update mechanism.

Never stop, adopt or alter stock Jolla or unrelated user processes, sockets,
configuration, libraries or homes. No `killall`, name-based `pkill`, global
`gpgconf --kill all`, default-home fallback or automatic private-home deletion.
Do not inspect key, password-store or OTP contents. Removal preserves private
homes and user data. A missing socket is not evidence of process absence.

This is lifecycle coordination for supported callers, not a security boundary
against the same user or root. Direct execution of private binaries bypasses
the current wrappers. A production maintenance design must explicitly address
such callers; an uncoordinated process scan cannot close an admission race.
Until the supported access model and its enforcement are reviewed, automatic
upgrade/removal acceptance remains blocked.

## States and ownership

| State | Required behavior |
| --- | --- |
| ACTIVE | Admit an operation against one stable installed payload generation; reuse only a verified current private agent. |
| DRAINING | Close admission before waiting; reject new operations with a clear retryable failure. Existing operations may finish within a declared deadline. |
| QUIESCENT | No admitted operation or runtime/helper process remains, no managed agent is running and its sockets are gone. Admission remains closed. |
| CHANGING | Only the package transaction owns the runtime payload; callers cannot execute a partially changed generation. |
| BLOCKED | Preserve closed admission after uncertainty, interrupted change, unexpected process, unverifiable identity or failed validation. Require explicit recovery. |

A privileged package-maintenance coordinator owns the global transition and
payload generation. Each supported client participates in the same admission
protocol for the full operation lifetime. Per-user agent control participates
as well. The implementation must define atomic admission/closure, crash-safe
ownership and recovery; a writable PID file or a lock released by client death
alone is insufficient when descendants survive. Root-owned maintenance state
must not be placed in a user-writable directory.

## Admission and normal agent use

1. Validate the explicit private home and configuration restrictions.
2. Acquire an operation registration atomically with the global admission check.
   Register the payload generation and public process identity; never record
   commands, secret arguments, key contents or environment dumps.
3. Validate any existing agent before allowing IPC. Check user, executable
   identity, exact managed launch arguments, private mappings and current file
   identities. Reject obsolete, foreign, malformed or unobservable state without
   trying to repair or terminate it automatically.
4. Keep the registration through all children and relevant helpers. Simultaneous
   starts for the same home must converge on one verified current agent, or fail
   safely. Close the check-to-use window against package payload changes.
5. Release the registration only when operation cleanup is established. Normal
   client exit may leave its verified agent running while ACTIVE.

Current policy checks provide useful preflight decisions, but they do not hold
a payload lease through execution or eliminate agent/socket replacement races.

## Interruption and stop

A stop request must distinguish graceful drain from explicit cancellation.
It cannot report successful quiescence while another operation is active.
A deadline expires into a reported blocked state; it must not silently force
kill unrelated processes or allow the package transaction to continue.

Track processes with PID plus kernel start identity and revalidate before any
signal. PID disappearance/reuse alone cannot establish cleanup of descendants.
An IPC watchdog must have a cleanup owner even if its invoking wrapper receives
TERM or KILL. TERM may be handled by the wrapper; KILL cannot rely on its traps.
Any surviving helper, orphan, stale socket or uncertain mapping keeps the
maintenance transition blocked. Observer cleanup in a test is not runtime cleanup.

## Upgrade, removal and recovery

1. Close admission globally, including users and homes without a connected
   socket; record the transaction generation before payload replacement.
2. Drain operations, then stop only positively identified managed private agents
   under their owning users. Never use secret-bearing home discovery.
3. Establish process/helper and socket quiescence, including surviving children
   after client death. An inaccessible process identity is uncertainty, not a
   negative result. Validate the supported access model against concurrent starts.
4. Only then permit payload replacement or removal. A late old-package cleanup
   hook cannot protect an already replaced executable or mapped library.
5. After upgrade, validate the complete new generation and entry points before
   reopening admission. After removal, keep entry points unavailable and retain
   user data. Do not automatically relaunch agents across generations.
6. A failed or interrupted change must not reopen admission by timeout or stale
   lock removal. Recovery inspects public transaction/process metadata, verifies
   one complete installed generation and requires explicit operator action.

The concrete package-manager/service integration is still to be designed and
reviewed. `%preun` alone and a successful `rpm --test` do not implement this
protocol. The existing inert RPM ordering probe requires separate installation
approval and has not been rerun for this proposal.

## Verification and acceptance

Use only isolated synthetic homes and inert subprocesses for host tests.
Changed-payload integration needs a separately approved disposable SDK test;
device acceptance uses an explicit target and separate scope. Do not reuse a
real user home, keyring or password store.

| Required scenario | Current evidence / remaining work |
| --- | --- |
| Current agent and strict launch identity | Host policy fixtures accept the controlled identity and reject extra options/other homes. |
| Foreign, deleted or changed executable/library | Host fixtures reject tested mismatches; real kernel mappings, ownership and races still need integration verification. |
| Missing, symlinked, non-socket or permissive socket; malformed IPC reply | Host policy fixtures verify these admission decisions. Socket absence returns 3, not successful stop. |
| Live-owner IPC timeout | Existing host observer confirms timeout cleanup in its bounded inert case. |
| Wrapper TERM/KILL during IPC | Observer reproduces surviving IPC; runtime cleanup is not established. |
| Concurrent starts, update drain and new-operation rejection | Requires shared admission implementation and race tests. |
| In-flight operation, orphan/helper, PID reuse and deadline expiry | Requires implementation plus controlled interruption/identity tests. |
| Changed executable/library upgrade and remove | Requires approved integration test with process/socket inventory and unrelated sentinels. Same-payload release bump is insufficient. |
| Failed transaction, interrupted coordinator and recovery | Requires crash/failure injection and proof admission remains closed. |
| Stock/user isolation and private data retention | Must be verified independently on the reviewed implementation; host fixtures alone do not establish it. |

[Baseline measurements](lifecycle-baseline-20261015.md) record exact source
identities, commands and limits. Passing builder tests are not independent
verification. Issue #3 remains open through implementation and verification
separate from implementation. Human source review does not imply release approval.

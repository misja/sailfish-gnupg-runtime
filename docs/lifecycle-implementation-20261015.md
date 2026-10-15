# Lifecycle implementation slice — 2026-10-15

Basis: reviewed [contract](lifecycle-contract.md), merged in PR #10 at
`ac206931dba69670490aae112c417d77b7112371`. Tracking: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).
This slice fixes direct IPC supervision and implements an experimental admission
primitive. Full wrapper/agent/package coordination remains open.

## Direct IPC supervision

`runtime_timed` now waits for a separate supervisor. That supervisor owns the
IPC helper and watchdog; loss of the calling wrapper does not change the helper's
parent identity. The existing PID/start-time/parent comparisons remain intact.
The supervisor continues until normal completion or the existing 15-second
timeout plus one-second termination grace. Only a temporary test copy shortens
the 15-second interval.

A successful helper preserves stdout and exit status. A watchdog timeout returns
124 even if the helper subsequently reports success. Unexpected watchdog failure
returns 78. The SDK exposed this distinction: emulated helper termination could
appear successful after TERM. The regression now checks a helper deliberately
handling TERM with exit zero.

The inert observer now supports `--require-cleanup`, making surviving IPC a test
failure. In both host and SDK measurements the direct helper was no longer alive
before observer cleanup in all three cases: live wrapper, wrapper TERM, wrapper
KILL. Live-owner timeout returned 124. The old policy failed the same regression.
This does not establish cleanup after the supervisor itself dies, arbitrary
helper descendants, daemon agents or a whole interrupted GnuPG operation.

## Experimental admission primitive

`runtime/lifecycle_admission.py` is a callable implementation exercised by tests.
It is not installed by the RPM or called by either wrapper. It introduces no
installed Python dependency or automatic state-directory creation at runtime.

The prototype uses a stable admission lock for the ACTIVE check and lease
registration, and a separate shared operation lock. Maintenance closes admission
under the first lock before waiting for exclusive ownership of the second.
Several operations may share one generation while ACTIVE. A generation is an
explicit SHA-256-shaped identifier; authenticating a complete installed payload
against it is still an integration responsibility.

`Lease.spawn` explicitly passes the operation descriptor to its child. Closing
the parent's copy does not unlock an inherited descriptor; a killed client can
therefore leave a registered, still-running child. A drain deadline produces
BLOCKED, and a killed coordinator leaves DRAINING. Neither state automatically
reopens admission. There is deliberately no resume/recovery API yet.

The directory/state/locks require the expected owner, fixed modes and canonical
non-symlink paths. Missing or invalid state is rejected. State transitions use
atomic replacement and fsync. Initialization is explicit, owner-only and never
replaces an existing lock directory. Tests use only their own temporary owner
and directory, supplied directly to the API; the production expected owner
default is root. Cross-user operation and real root-owned deployment still need
separate verification. Atomic-write code is not evidence of power-loss recovery.

DRAINED is an internal lease-only result, **not QUIESCENT** and not permission to
change packages. A child that closes the descriptor, an unregistered caller or
a persistent agent can outlive the registered operation. Wrapper wiring must
resolve those cases before package transactions use this primitive. Direct
callers, global ownership across reboot, agent control, payload verification,
trusted state initialization and recovery remain integration work. Runtime
language/dependency choice must be reviewed before shipping the primitive.

## Executed verification

- Host: all 39 runtime repository tests passed.
- Existing SDK 3.13.5 / SailfishOS-5.1.0.11-aarch64: 34 selected policy, admission
  and IPC tests passed. Five package/source fixture tests ran on the host only.
- Both environments: live-owner/TERM/KILL inert observer cases passed with
  `--require-cleanup`. The original policy regression returned the expected
  failure on the host only.
- All six staged SDK input file hashes match the review worktree. Exact hashes
  and bounded results are in the [machine-readable record](lifecycle-implementation-20261015.json).
- Shell syntax, local document links and whitespace checks passed.

Commands from the repository root:

```sh
python3 -m unittest discover -s tests -q
python3 tools/test-interrupted-watchdog.py --require-cleanup --output /tmp/lifecycle-result.json
```

SDK tests staged only the six recorded files in a new `build/lifecycle-review`
directory within the existing clean-build checkout. The selected tests used
`TMPDIR=/home/ubuntu/sflc-tmp-20261015`: Scratchbox2's physical `/tmp` path caused
the strict socket-parent check to reject one initial fixture; using a long shared
work path then exceeded the Unix-socket path limit. A short shared fixture path
resolved both without relaxing production checks. The first SDK observer also
failed the live-owner exit-status requirement, leading to the explicit timeout
result and its regression test above. These earlier failures are not counted as
passes.

No cryptographic operation, real user store/home inspection, package rebuild,
installation, device/OBS action or upstream submission occurred. These are
implementation self-tests, not independent security or release verification.
The source changes are prepared for maintainer review; issue #3 remains open.

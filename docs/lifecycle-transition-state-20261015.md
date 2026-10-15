# Generation-transition state — 2026-10-15

Basis: draft [PR #13](https://github.com/misja/sailfish-gnupg-runtime/pull/13),
`f55de2d6da3ad3213b8d18e18f03de7e7360b9d1`. This continuation requires its review.
Tracking: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).

This slice implements internal state-machine primitives. No new administrative
command, package writer, RPM scriptlet or installation path is enabled.

## Recorded destination and reconciliation

`Controller.prepare_transition(target)` requires DRAINED admission, exclusive
bootstrap/operation/agent locks, no detected private processes/mappings, and the
verified original payload. The caller supplies the exact SHA-256 of the reviewed
destination manifest; the controller does not derive approval from newly installed
bytes. Same-generation and malformed targets are refused. Origin authentication
and human authorization of that destination remain external requirements.

The controller atomically replaces and fsyncs one state record:

```json
{"state": "UPDATING", "generation": "<original SHA-256>", "target": "<destination SHA-256>"}
```

Both hashes must be distinct, lowercase, 64-character SHA-256 values. Ordinary
states retain their original two-field format. Old readers reject UPDATING.
The original generation remains authoritative until reconciliation succeeds.
No separate journal/state pair can disagree across an interrupted write.

UPDATING refuses operation admission, agent stop, another preparation, ordinary
close and ordinary recovery. A failed verification retains the entire pending
record, including both identities. Existing lock files are never replaced.

`Controller.reconcile_transition()` excludes bootstrap/operation/agent leases,
checks process metadata and verifies only the recorded destination. Explicit
`restore=True` instead requires the exact original payload, including its
manifest. It does not restore files itself. Successful verification atomically
writes ACTIVE with the chosen generation and drops the completed intent. A
partial replacement or an unrelated regenerated manifest authorizes neither path.

## Deliberate integration boundary

These methods release locks when they return. UPDATING persists admission closure,
but does not prevent an invocation from loading Python or prevent an external
writer from changing files. They must not be used as a standalone upgrade recipe.
A future coordinator must retain bootstrap exclusion across the complete payload
mutation and reconciliation, supervise all writer descendants, and establish
writer absence before reopening. These primitives do not provide that proof.
A destination string supplied by a root caller is not evidence of source review
or package-signature verification. They are intentionally absent from the CLI.

Interrupted package-manager recovery, removal, legacy migration, arbitrary
unregistered callers, actual root/proc access, device integration and independent
security verification remain open. There is no generic root command runner and
no automatic acceptance of whatever generation is present after a failure.

## Implementation checks

The added synthetic tests cover destination completion, explicit original
restoration, partial and unexpected payloads, immutable pending intent, busy
bootstrap/agent registrations, private processes, malformed state, fresh-controller
reconciliation and retained lock inodes. Fault injection before and after atomic
replacement checks the surviving record. A real forked preparer is killed with
SIGKILL after persistence; admission stays closed and explicit original restoration
is possible. These are process-interruption checks, not power-loss simulation.

Executed test counts and staged input hashes are recorded in the adjacent
[bounded evidence](lifecycle-transition-state-20261015.json). All fixtures are
synthetic. No real GnuPG operation, root lifecycle state, dependency installation,
RPM build/install, device/OBS change or upstream submission occurred. Builder
checks do not constitute independent security or release verification.

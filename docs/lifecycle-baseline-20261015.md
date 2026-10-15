# Lifecycle baseline — 2026-10-15

Implementation base: `770610019f64245d128ee9a2108495ef71910320`.
The proposed [lifecycle contract](lifecycle-contract.md) is not implemented by
this baseline. No runtime wrapper or RPM recipe is changed in this proposal.

## Executed checks

Host: Linux, actual `/usr/bin/busybox sh`. No GnuPG executable or real home,
key, password-store, OTP input, package installation or device operation was used.

`python3 -m unittest discover -s tests -v`: 20 tests passed, including 15 new
agent-policy cases. The tests execute the unchanged policy functions against
controlled temporary proc-like metadata, inert file identities, executable IPC
stubs and actual temporary Unix sockets. They do not inspect real agent metadata.
The test overrides `private_prefix` and `proc_root` after sourcing the policy;
these are fixture substitutions, not new production environment overrides.

Positive checks accept a current fixture identity and a socket/PID/current-agent
combination. Negative checks cover replaced/deleted executable paths, unmanaged
launch options, another home, stock crypto paths, deleted/replaced mappings,
a missing required mapping, invalid PIDs, absent or unsafe sockets and malformed
IPC response. Ownership rejection across UIDs and real proc races are not tested.

`python3 tools/test-interrupted-watchdog.py --output /tmp/sailfish-lifecycle-watchdog-20261015.json`:
existing observer ran all three cases. A temporary policy copy shortens only the
15-second timeout to one second. Each case has a separate observer-owned process
group with guaranteed final observer cleanup. The bounded
[machine-readable result](lifecycle-watchdog-20261015.json) includes source hashes.

| Case | Owner exit | IPC alive after observation | Meaning |
| --- | --- | --- | --- |
| Owner alive | 137 | no | Watchdog terminated inert IPC in this case. |
| Owner TERM | -15 | yes | Wrapper cleanup not established; observer removed it. |
| Owner KILL | -9 | yes | Wrapper cleanup not established; observer removed it. |

These last two outcomes are measured defects/boundaries, not successful runtime
cleanup tests. The IPC fixture ignores TERM; after wrapper death its parent
identity changes, and the watchdog identity check does not establish termination.
This finding alone does not authorize weakening identity checks.

## Consequences

There is no shared operation admission or package maintenance coordinator in the
current wrappers. The current runtime RPM has no lifecycle scriptlets. Even
successful strict preflight and bounded stop cannot establish quiescence while
another client may start or survive. A source merge of this proposal therefore
cannot close issue #3, permit automatic upgrade/removal or change support claims.

The legacy RPM ordering probe and lifecycle summary remain historical tools;
they were not executed here. No changed-payload upgrade, native provider test,
Sailfish 5.2/device acceptance or independent security verification is claimed.

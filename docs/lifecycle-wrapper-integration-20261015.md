# Wrapper and persistent-agent admission — 2026-10-15

Basis: PR #11, merged as `9ec4a0fa72c2c9c55638fc03e227e723410e5046`.
Tracking: [runtime #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).
This slice connects both public entry points to admission and distinguishes
operation lifetime from persistent-agent lifetime. Complete package maintenance
and release acceptance remain open.

## Entry points and process ownership

Both BusyBox wrappers sanitize the environment and invoke the fixed installed
`lifecycle-entry.py` through `/usr/bin/python3 -I -B`. State and helper paths are
fixed; there is no environment or command-line path/UID override. Python 3 is a
new explicit RPM dependency. Its availability/footprint on a device has not been
verified. Python bytecode writes are disabled for public wrapper invocation.

The former shell logic lives in `gpg-operation` and `agent-operation`. A separate
Python guardian acquires admission before starting either helper, holds the
operation registration until that direct child exits and waits through caller
TERM/KILL. The guardian handles TERM/INT/HUP without releasing registration early;
its exec'd operation child retains ordinary signal behavior. This does not prove
cleanup of arbitrary descendants or survive KILL of the guardian itself.

The shell policy still validates the explicit private home, agent executable,
launch options, sockets and current private mappings. A dedicated reporting pipe
carries only a verified PID and kernel start identity to the guardian. GnuPG
stdin/stdout and secret-bearing arguments are not used as registration data or
logged. Unexpected/missing identity reports cannot turn a successful child exit
into successful admission.

Normal GnuPG operations explicitly establish and register a managed agent first.
The actual GnuPG invocation has `--no-autostart`, preventing an unregistered
replacement if that agent disappears. Explicit caller `--no-autostart` is honored:
a missing-agent preflight is reported as `absent` and no agent is started. Exact
single-argument `--version`, `--help` and `--dump-options` remain passive.
This changes normal startup: an otherwise non-passive operation establishes an
agent even if that particular GnuPG command would not itself have needed one.
The pinned GnuPG 2.5.24 source defines `no-autostart` and no positive `autostart`
option in its CLI parser; no upstream code or source pin changed.

## Persistent agents and stop

A detached watcher holds a separate shared `agents.lock` registration while the
reported UID/PID/start identity remains alive. It observes public kernel identity
only and never signals that process. Unreadable/uncertain identity retains the
registration. On confirmed disappearance, identity change or zombie state it
releases the registration. That release is not a claim that all sockets or
unrelated helpers are gone.

A stable, empty mode-0600 `.sailfish-agent-watch-<generation>-<pid>-<start>.lock`
in the validated private home prevents a new watcher per client call. The home
must remain canonical, owned by the caller and mode 0700; symlinks, hard-linked
or unsafe lock files are rejected. The watch retains only its agent and dedup
lock descriptors, closes inherited operation/reporting descriptors and redirects
standard streams to `/dev/null`. Old empty lock files are retained rather than
unlinked while another caller may hold them. They contain no key/configuration
material; lifecycle cleanup policy for them remains to be decided.

Agent `stop` obtains exclusive operation access. While another operation is
active it returns retryable status 75 instead of interrupting that operation.
Normal entry requires ACTIVE; stop is also allowed in DRAINED so that agents can
be shut down after operation drain. It is rejected in DRAINING/BLOCKED. A stop
never reopens admission. The original strict agent/socket checks still decide
which endpoint can receive `KILLAGENT`.

DRAINED continues to mean **operation leases only**. An agent can remain
registered after drain, and an unregistered process or failed watcher can exist
without a lease. Before changing packages, the future privileged coordinator
must establish complete process/socket quiescence, including direct callers,
monitor failure and surviving descendants.

## Packaging and deployment boundary

The candidate recipe is now release `0.4`, installs both public wrappers and five
private helper/module files, and declares `/usr/bin/python3`. The RPM inspector
checks their exact source bytes/modes and corresponding-source inclusion. No
RPM scripts initialize state, upgrade packages or modify user data.

The fixed state directory is `/var/lib/sailfish-gnupg-runtime`, with root-owned
admission/operation/agent locks and state. Missing, closed or unsafe state causes
refusal before executing the operation helper. No automatic initialization or
fallback exists. The `Admission.initialize` API is still a primitive, not a
reviewed deployment/bootstrap procedure: its supplied generation is not yet
verified against the installed payload. Do not treat calling it manually as
production acceptance. Trusted bootstrap, generation authentication, recovery
and the initial code-load/update boundary require the next implementation.
Consequently this candidate must not be installed on a device as a ready upgrade.
Existing device packages were not changed.

## Executed checks

- All 55 host runtime tests passed.
- All 50 selected SDK tests passed using SDK 3.13.5 and installed
  SailfishOS-5.1.0.11-aarch64. The five source/package fixtures ran on the host.
- The current policy passed all three inert IPC observer cases in that SDK.
- Public-wrapper fixtures verify caller TERM/KILL while the operation closes
  inherited descriptors, persistent agent registration after operation drain,
  repeated-call watch reuse, exclusive stop and stop after DRAINED, passive/no-
  autostart handling, malformed reports and missing/closed state.
- Admission tests also verify attaching an agent during DRAINING on behalf of
  an already admitted operation. This cannot prematurely complete operation drain.
- SDK execution of the actual install fragment staged seven exact files with
  expected modes; `rpmspec -P` parsed release 0.4 and the Python dependency. The
  fragment now explicitly creates its private helper destination. A temporary
  checker quoting error and an empty-stage destination failure were corrected
  before the successful staging result. No full RPM build was performed.
- Shell syntax, Python parsing, relative document links and whitespace passed.

Test copies alone substitute fixed prefix/state/owner constants so fixtures use
only temporary directories and inert agents. Installed code exposes no such
substitution interface. The controlled private-home fixtures contain no keys,
password stores or OTP material. All staged SDK input hashes match the review
worktree; the [bounded result record](lifecycle-wrapper-integration-20261015.json)
records identities and scope.

No real GnuPG operation, package/dependency/target installation, device/OBS action
or upstream submission ran. These are implementation self-tests, not independent
security verification. Issue #3 remains In Progress through trusted maintenance,
changed-payload integration and verification separate from implementation.

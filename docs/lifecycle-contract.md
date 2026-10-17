# Runtime upgrades and removal

Owner: Misja Hoebe. Tracking: [issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3).
Scope: the separately packaged `sailfish-gnupg-runtime`; Jolla’s GnuPG and agents
are not part of its lifecycle.

## Agent lifetime across updates

GnuPG starts private agents on demand. Do not add systemd socket supervision:
the pinned GnuPG 2.5.24 README discourages it because it conflicts with GnuPG’s
own activation. The inspected Sailfish SDK systemd 238 user-restart RPM macro
also performs no action. Familiar service macros alone do not solve this task.

A legitimate private agent may continue after RPM replaces its executable or
libraries. The wrapper verifies its user, selected home, socket, launch arguments,
exact private executable path and the private origin of required libraries.
It permits the kernel's literal `(deleted)` suffix on replaced file mappings;
it does not require those mappings to equal newly installed filesystem inodes.
This identifies the private runtime origin, not its precise historical version.
It is not a security boundary against a compromised process of the same user.

An existing agent keeps its old code until it exits. Installing a security fix
does not make that fix active in an already running agent. The policy change
removes an unnecessary rejection after updates; it is not proof of arbitrary
cross-version compatibility or automatic restart/upgrade coordination.

## Package removal

Only final removal runs the `%preun` hook (`$1 = 0`). Installation and upgrades
have no start/stop hooks. GnuPG continues to manage activation itself.

The hook first checks public `/proc/PID/exe` identities for supported private
command-line clients/helpers. If any are found, it refuses removal before
sending signals and asks the user to close the application and retry. Otherwise
it sends one TERM request to agents identified by the exact private executable
path, including a replaced executable marked `(deleted)`. It checks the identity
again before signalling. No homes, key contents, command arguments or process
environments are inspected.

The hook does not wait for or force termination, and does not fail after sending
shutdown requests. This avoids repeatedly signalling a busy agent on automatic
retry: the pinned GnuPG forcibly exits after its third TERM. Direct Assuan clients
are outside CLI detection and may be interrupted. This is a shutdown request,
not a guarantee that every agent exited or that concurrent new starts are
excluded. No registry, lock, watcher or service framework is introduced.

Normal-user removal does not require finding or killing processes manually.
Never stop Jolla or unrelated processes or delete key homes/stores. A missing
socket does not prove process absence. Package hooks use executable identity;
name-only killall is inappropriate because Jolla also runs gpg-agent, and
current-file-only selectors miss agents whose old executable was unlinked.

Host fixture tests cover actual signal selection, busy refusal before signals,
retries, deleted executable matching and stock-process preservation. A bounded
SDK-emulated GnuPG probe did not demonstrate TERM handling (no handler log or
exit observed); do not label that a successful native shutdown test. Focused
confirmation on the actual target remains due before shipping the hook. This
is not a request to repeat complete Xperia acceptance.

Historical lifecycle implementation/probe records retain their original scope;
they are not acceptance of the current removal behavior. The remaining task is
tracked in the existing issue, not a new lifecycle specification or backlog.

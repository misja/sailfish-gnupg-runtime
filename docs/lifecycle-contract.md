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

## Removal and remaining package integration

No lifecycle scriptlets or service framework have been added by this change.
Automatic coordination of running clients and agents during package removal
remains unresolved. Normal-user installation/removal must not require finding
or killing processes manually; do not present a development workaround as the
finished package behavior.

Never stop stock Jolla or unrelated user processes, delete key homes, or infer
process absence from a missing socket. User keys and stores must survive removal.
Changes to package hooks must follow demonstrated upstream/platform practice and
receive independent review. Do not add a coordinator, registry, marker/locking
framework or deprecated supervisor merely to preserve a project-specific rule.

Historical lifecycle implementation/probe records retain their original scope;
they are not acceptance of the current removal behavior. The remaining task is
tracked in the existing issue, not a new lifecycle specification or backlog.

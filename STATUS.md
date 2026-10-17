# Current source status

Experimental source; general release acceptance remains open.
[Issue #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3) and the project
board own live work and review status.

Cleanup removes the custom Python admission, guardian/watch, generation and
recovery framework, its tests, manifest build hooks and experimental RPM probes.
The shell wrappers retain private paths, strict home/agent checks and bounded
IPC supervision. Candidate 0.6 requires neither Python nor flock at runtime.

See the [maintenance policy](docs/lifecycle-contract.md). Automatic upgrade/removal,
global start exclusion and independent verification remain unresolved. This is
not a device-ready upgrade. No installed package, state or user data was changed.

Build handoff, 2026-10-16: candidate 2.5.24-0.6 built from clean public main
`46e5b60d2281cc6e7bd376924ca0caf5d63354e1` in the existing SDK 3.13.5 /
SailfishOS-5.1.0.11-aarch64 target. Binary/source inspection passed, including
14 private-path ELF objects and removal of lifecycle files and Python/flock
runtime requirements. Exact hashes, commands and limitations are in the
[bounded build record](docs/build-records/runtime-06-20261016.json).
No installation, new lifecycle experiment or device acceptance is implied.
A separate assistant recomputed hashes and checked RPM metadata/ownership and
reviewed the inspector; no blocker was found for this bounded packaging result.
This is separate assistant verification, not a human security audit or release approval.

Documentation clarification: README now explains separate package/command/library/
keyring/agent paths alongside Jolla GnuPG, and scopes maintenance restrictions to
the private runtime. Native graphical integration is described separately.
Release Manager wording and independent technical documentation review are tracked
in workspace release issue #2. No runtime code or package contents changed.

2026-10-17 package correction in progress: rename source to
sailfish-gnupg-runtime 2.5.24-0.7; coordinated pass/OTP revisions 0.6.
Current build tools/tests updated; historical evidence/draft artifacts untouched.
Existing 23 runtime and four pass packaging tests passed. Rename scope reviewed.
Lifecycle remains unimplemented pending agreement on upstream-aligned agent
behavior: current inode/generation checks are a project-specific constraint,
not necessary for namespace coexistence. Pinned GnuPG discourages supervised
systemd activation; SDK238 user restart macros are ineffective. No custom
marker/locking/coordinator is authorized as a workaround. See runtime issue #3.

Targeted agent-origin correction: separate scope and source review passed.
Private agents with replaced executable/library mappings are no longer rejected
solely because their files differ from the new installation. UID/home/socket/
launch-argument/private-origin checks remain. All 27 synthetic host tests passed.
No scriptlets, restart guarantee, device acceptance or artifact refresh claimed.
Research-first instruction copied to all local AGENTS baseline 1.3.0 locations.

Final-removal hook proposed: %preun0 refuses detected private CLI clients before
signals, otherwise requests one TERM for exact private agent executables (also
previous deleted files). No install/update hooks, no wait/escalation/state.
Host fixtures validate control flow and signal selection; SDK-emulated actual
agent TERM probe was inconclusive and is not target acceptance. Separate source
review is required; current signed draft assets have not been rebuilt/replaced.

Native confirmation, 2026-10-17: the dev Xperia5.2.0.20 passed busy refusal,
upgrade skip, idle TERM shutdown and deleted-executable TERM shutdown using only
synthetic agents/empty homes in an isolated temporary prefix. Jolla hashes and
process snapshot unchanged; fixture agents/files cleaned. One process scan now
replaces the redundant two scans. Separate source/evidence review passed.
See docs/lifecycle-confirmation-20261017.json; actual new0.7RPM transactions and
full candidate acceptance are not claimed. Existing draft artifacts unchanged.

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

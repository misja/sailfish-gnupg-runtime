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

Design handoff, 2026-10-16: Architect proposal and separate reviewer assessment
for the [bounded maintenance boundary](docs/lifecycle-contract.md) are recorded
in its PR under #3. Scope: cold replacement of a dedicated disposable instance,
not live RPM upgrades or a new coordinator. No implementation or experiment ran.
Misja remains decision owner; evidence and release gates stay open.

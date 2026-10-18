# Current source and delivery

Updated: 2026-10-18. Live work: [runtime #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3)
and [workspace delivery #2](https://github.com/misja/sailfish-workspace/issues/2).
Misja decides merge/publication. The Release Manager owns documentation and
release presentation; an independent reviewer checks technical evidence.

The candidate is `sailfish-gnupg-runtime` 2.5.24-0.7, coordinated with pass
1.7.4-0.6 and OTP 1.2.0-0.6. The name changes; private executable/library paths
remain unchanged. Existing verified agents may retain their old code across
updates. Final removal refuses detected private CLI clients before requesting
private-agent shutdown. There are no installation/update hooks or service framework.
See the [maintenance policy](docs/lifecycle-contract.md).

The exact removal hook passed a focused synthetic check on the development
Xperia running Sailfish OS 5.2.0.20: busy refusal, upgrade skip and shutdown of
idle agents, including replaced executables. Temporary files and agents were
cleaned; Jolla files/processes were preserved. This did not install the new RPM.
See [the confirmation record](docs/lifecycle-confirmation-20261017.json).

The SDK build and inspection are recorded in
[the current build record](docs/build-records/runtime-07-20261017.json).
The [0.6 record](docs/build-records/runtime-06-20261016.json) retains historical
artifact identities. The existing unpublished draft now contains the reviewed 0.7
runtime with signed binary/source RPMs and public certificate (three assets).
Pass/OTP 0.6 was refreshed with it. SDK signature verification and separate
cryptographic assistant review passed; separate final draft/download review
found no blocker, with all thirteen downloads matching local delivery hashes.

[Runtime PR #22](https://github.com/misja/sailfish-gnupg-runtime/pull/22) awaits
maintainer review; the [runtime draft](https://github.com/misja/sailfish-gnupg-runtime/releases/tag/untagged-8a6ad3eb9eb59c1e39d0)
retains source `58dde123489134a67e92306ce46d6c097ce1b8f7`.
The delivery evidence and cleanup confirmation remain in the parent workspace's
`.local-artifacts/release-20261017-cli/`. The Release Manager records the final
handoff in workspace #2 and runtime #3. Next: Misja's review and later explicit
publication decision. Assistant review is not a human audit or release approval.
No merge, publication, full Xperia retest or new installation/device change.
Native graphical integration has separate source/provider work.

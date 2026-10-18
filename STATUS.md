# Current source and delivery

Updated: 2026-10-17. Live work: [runtime #3](https://github.com/misja/sailfish-gnupg-runtime/issues/3)
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
artifact identities. Current signed GitHub drafts still contain the 0.6 runtime
and 0.5 pass/OTP files until the reviewed replacement set is uploaded.

Next: finish independent artifact/signature review and refresh the drafts,
including coordinated-update instructions. No full Xperia retest or automatic
publication. Native graphical integration has separate source/provider work.

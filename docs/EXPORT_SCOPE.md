# Source snapshot and build prerequisites

This repository starts with selected prototype sources. Original operational
history, raw test reports, device inventories and binary/source archives are
kept separately. The initial commit identifies the local source basis; it
does not import that repository's original Git history.

Source identities are pinned in sources.lock.json where present. Obtain and
authenticate the upstream archives, public release keys and signatures before
building. A private key is not a build input.

Public source archives and verification records can be recreated with the
sibling workspace's tools/fetch-sources.py. It uses temporary public-only keyrings
and preserves the existing archive/version/signer pins. See the
[public source bootstrap guide](https://github.com/misja/sailfish-workspace/blob/main/docs/development/source-bootstrap.md).
Generated sources/ and evidence/ inputs are ignored; do not copy historical
private trial evidence to satisfy staging.

SDK build entry points accept SAILFISH_SDK_ROOT and require an explicit
SAILFISH_SDK_TARGET. Follow the ordinary official SDK route, normally Docker
directly on Linux. The maintainer's outer LXC container is optional. Historical
test harnesses can still have fixed paths; the clean SDK build and main source/binary RPM inspections are recorded in
[the build report](https://github.com/misja/sailfish-workspace/blob/main/docs/development/clean-sdk-build-20261015.md).
The bootstrap fixes have been merged; see the linked build report. Auxiliary debug-package
delivery and release acceptance remain separate. Native vendor-source and relink inputs
are separate gates.

The CLI runtime is a separately named package alongside Jolla’s GnuPG, with
separate commands, libraries, keyring and agent; see the [overview](../README.md).
Earlier synthetic Xperia tests and the later OS-update package-preservation
check remain part of its evidence. Runtime lifecycle and provider/upgrade work
remain open. Exact vendor-source mapping concerns the separate native integration.

Original work is GPL-3.0-or-later, copyright (c) 2026 Misja Hoebe. See
[LICENSING](../LICENSING.md) and [upstream exceptions](../THIRD_PARTY.md).
Source publication is separate from package releases, device changes and
upstream submissions.

Current runtime uses the shell wrappers and bounded IPC supervisor. The custom
Python admission/watch/generation/recovery layer and payload-manifest RPM hooks
have been removed. Python remains a build/test tool, not an installed runtime
requirement. See the [maintenance policy](lifecycle-contract.md): no global
start exclusion or supported automatic upgrade/removal path is implemented.
No device installation is approved by these source changes.

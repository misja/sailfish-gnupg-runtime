# GnuPG runtime for Sailfish OS

GnuPG 2.5.24 packaged alongside Sailfish OS’s existing GnuPG, for pass and
other applications that explicitly select it.

## Why this project

The Sailfish SDK environment examined by this project includes a GnuPG package
based on 2.0.4. Newer OpenPGP key workflows, including Ed25519 and Curve25519,
motivate a modern engine alongside the existing system stack.

The aim is to provide that engine while preserving Jolla's system binaries,
libraries and agent configuration. Keeping it separate lets compatibility and
distribution requirements be reviewed without changing core OS packages.
[Background](docs/BACKGROUND.md) explains the version and licensing context.

A practical goal is to use [pass and pass-otp](https://github.com/misja/sailfish-password-store)
as a password and OTP store on Sailfish OS.

## Alongside Jolla’s GnuPG

The `sailfish-gnupg-private` package does not replace Jolla’s GnuPG:

| | This package | Jolla’s installation |
| --- | --- | --- |
| Commands | `sailfish-gpg`, `sailfish-gpg-agent` | Existing `gpg` and agent commands |
| Programs and bundled libraries | `/usr/libexec/sailfish-gnupg` | Existing system paths, left in place |
| Keys and user state | Separate directory selected with `SAILFISH_GNUPGHOME` | Existing `~/.gnupg` and configuration |
| Agent | Separate agent and sockets for the selected private home | Existing agents, left in place |

Applications choose this runtime explicitly; installing it does not redirect the
system `gpg` command. The launchers require an explicit private home and refuse
the account’s default `~/.gnupg`. Existing keys are not imported automatically.
The [pass/OTP packages](https://github.com/misja/sailfish-password-store) are
configured to use this runtime.

Work on Jolla’s graphical password prompt is maintained separately in the
Sailfish Secrets fork. That integration is not part of this CLI package.

## Updating this package

The maintenance restriction concerns `sailfish-gnupg-private`, not Jolla’s GnuPG.
Replacing its files while applications or its private agents are running can
leave them using different versions of the runtime. Automatic coordination of
those processes during upgrade/removal is not implemented.

Before changing this package, ongoing operations must finish, new use must be
prevented and its private agents must be stopped. Do not stop Jolla’s agents.
This is not yet a supported general upgrade procedure; see the
[maintenance notes](docs/lifecycle-contract.md) for the remaining constraints.

## Source and status

Runtime launchers, RPM recipes, source locks and build/test tools live here.
Native pinentry adaptations live in the [Sailfish Secrets fork](https://github.com/misja/sailfish-secrets);
[the pinned source map](integrations/native-pinentry/sources.json) identifies
the upstream base and separate compatibility/prototype branches. Prototype
source files are generated from those commits rather than maintained as copies.

Start with the [documentation index](docs/index.md). Production agent lifecycle,
exact vendor-source provenance, provider compatibility and upgrade/removal
behavior remain open. Earlier builds were tested with synthetic data on an
Xperia running Sailfish OS 5.2.0.18; package preservation was checked after its
update to 5.2.0.20. The current revisions have SDK build/regression evidence.

Development uses AI-assisted tools under maintainer review; see
[CONTRIBUTING](CONTRIBUTING.md). Original work is [GPL-3.0-or-later](LICENSING.md);
[upstream licenses](THIRD_PARTY.md) remain in force.

See [fork and packaging maintenance](docs/FORK_WORKFLOW.md).

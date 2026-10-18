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

The `sailfish-gnupg-runtime` package does not replace Jolla’s GnuPG:

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
[Sailfish Secrets compatibility branch](https://github.com/misja/sailfish-secrets/tree/sailfish/native-pinentry-compat).
That integration is not part of this CLI package.

## Updating this package

If pass/OTP is installed, update the runtime, pass and pass-otp together in the
same package transaction; the packages have coordinated version dependencies.

Existing private agents continue running across package updates. They use their
previous code until they exit; a new agent uses the installed fixes. Jolla’s
GnuPG and agents remain unchanged.

Removal asks the runtime’s private agents to shut down. If a supported
command-line operation is detected, removal stops with a message to close the
application and try again. Jolla’s agents and your stored keys are left alone.
See the [maintenance notes](docs/lifecycle-contract.md) for the limits of this
shutdown request.

## Source and status

Runtime launchers, RPM recipes, source locks and build/test tools live here.
For the graphical password prompt, [the pinned source map](integrations/native-pinentry/sources.json) identifies
the upstream base and separate compatibility/prototype branches. Prototype
source files are generated from those commits rather than maintained as copies.

Start with the [documentation index](docs/index.md). The removal hook was checked with synthetic agents on the development Xperia
running Sailfish OS 5.2.0.20. Native integration has separate vendor-source and
provider requirements. Earlier builds were tested with synthetic data on an
Xperia running Sailfish OS 5.2.0.18; package preservation was checked after its
update to 5.2.0.20. The current revisions have SDK build/regression evidence.

Development uses AI-assisted tools under maintainer review; see
[CONTRIBUTING](CONTRIBUTING.md). Original work is [GPL-3.0-or-later](LICENSING.md);
[upstream licenses](THIRD_PARTY.md) remain in force.

See [fork and packaging maintenance](docs/FORK_WORKFLOW.md).

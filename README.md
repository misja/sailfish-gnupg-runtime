# GnuPG runtime for Sailfish OS

GnuPG 2.5, packaged alongside Sailfish OS's own GnuPG, for pass and other
applications that select it explicitly.

The Sailfish OS 5.1.0.11 SDK target has GnuPG 2.0.4, which predates
Curve25519 keys (added in GnuPG 2.1.7). This package adds GnuPG 2.5 without
changing the system's GnuPG. [Background](docs/BACKGROUND.md) covers the
versions and licensing.

## Alongside Jolla's GnuPG

The `sailfish-gnupg-runtime` package does not replace Jolla's GnuPG:

| | This package | Jolla's installation |
| --- | --- | --- |
| Commands | `sailfish-gpg`, `sailfish-gpg-agent` | Existing `gpg` and agent commands |
| Programs and bundled libraries | `/usr/libexec/sailfish-gnupg` | Existing system paths, left in place |
| Keys and user state | Separate directory selected with `SAILFISH_GNUPGHOME` | Existing `~/.gnupg` and configuration |
| Agent | Separate agent and sockets for the selected private home | Existing agents, left in place |

Applications choose this runtime explicitly; installing it does not redirect the
system `gpg` command. The launchers require an explicit private home and refuse
the account's default `~/.gnupg`. Existing keys are not imported automatically.
The [pass/OTP packages](https://github.com/misja/sailfish-password-store) are
configured to use this runtime.

This package asks for passphrases in the terminal; it has no graphical
password prompt.

## Updating this package

If pass/OTP is installed, update the runtime, pass and pass-otp together in the
same package transaction.

Existing private agents continue running across package updates. They use their
previous code until they exit; a new agent uses the installed fixes.

Removal asks the runtime's private agents to shut down. If a supported
command-line operation is detected, removal stops with a message to close the
application and try again. Jolla's agents and your stored keys are left alone.
An application that talks to the agent directly, without the command line, can
be interrupted by removal.

## Source

Runtime launchers, RPM recipes, source locks and build/test tools live here.
Work on a graphical password prompt is in the
[Sailfish Secrets compatibility branch](https://github.com/misja/sailfish-secrets/tree/sailfish/native-pinentry-compat);
[the pinned source map](integrations/native-pinentry/sources.json) identifies
its upstream base. Prototype source files are generated from those commits
rather than maintained as copies. Start with the
[documentation index](docs/index.md).

Development uses AI-assisted tools under maintainer review; see
[CONTRIBUTING](CONTRIBUTING.md). Original work is [GPL-3.0-or-later](LICENSING.md);
[upstream licenses](THIRD_PARTY.md) remain in force.

See [fork and packaging maintenance](docs/FORK_WORKFLOW.md).

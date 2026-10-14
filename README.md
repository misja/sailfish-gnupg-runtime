# GnuPG runtime for Sailfish OS

Experimental packaging of GnuPG 2.5.24 in an isolated runtime, with native
Sailfish pinentry integration.

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

## Source and status

Runtime launchers, RPM recipes, source locks and build/test tools live here.
Native pinentry adaptations live in the [Sailfish Secrets fork](https://github.com/misja/sailfish-secrets);
[the pinned source map](integrations/native-pinentry/sources.json) identifies
the upstream base and separate compatibility/prototype branches. Prototype
source files are generated from those commits rather than maintained as copies.

Start with the [documentation index](docs/index.md). Production agent lifecycle,
exact vendor-source provenance, provider compatibility and upgrade/removal
behavior remain open. Earlier 5.2.0.18 testing does not establish support for
5.2.0.20; this is not a supported general installation.

Development uses AI-assisted tools under maintainer review; see
[CONTRIBUTING](CONTRIBUTING.md). Original work is [GPL-3.0-or-later](LICENSING.md);
[upstream licenses](THIRD_PARTY.md) remain in force.

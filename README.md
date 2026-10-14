# GnuPG runtime for Sailfish OS

Experimental packaging of GnuPG 2.5.24 in an isolated runtime, with explicit launchers and native Sailfish pinentry compatibility patches. The private runtime is designed to coexist with Jolla's crypto packages.

The repository contains runtime launchers, RPM recipes, source locks, build and test tools, and native pinentry source and patches. Start with the [documentation index](docs/index.md); runtime/, rpm/, tools/ and integrations/ contain the implementation.

Production agent lifecycle, exact vendor-source provenance, provider compatibility and upgrade/removal behavior remain open. The SDK build target is 5.1.0.11/aarch64; earlier testing on 5.2.0.18 does not establish support for 5.2.0.20. This is not a supported general installation.

Development uses AI-assisted tools under maintainer review. See [CONTRIBUTING](CONTRIBUTING.md) for review and testing requirements. Shared working agreements live in [sailfish-workspace](https://github.com/misja/sailfish-workspace).

Original work is [GPL-3.0-or-later](LICENSING.md). Sailfish and other [upstream licenses](THIRD_PARTY.md) remain in force.

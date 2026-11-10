# Version and licensing background

The project SDK inventory recorded gnupg2 2.0.4+git6-1.8.4.jolla in the
SailfishOS-5.1.0.11-aarch64 target. That observation is scoped to the examined
SDK environment; a version label alone does not establish the patch content,
security status or package behavior of every Sailfish release.

GnuPG 2.1 and later support Curve25519; for example, [upstream introduced Curve25519 encryption in GnuPG 2.1.7](https://lists.gnupg.org/pipermail/gnupg-users/2015-August/054092.html).
The package recipes and source lock keep the selected versions explicit.

Licensing is part of the distribution context. [GnuPG 2.0.5 switched to GPLv3](https://lists.gnupg.org/pipermail/gnupg-announce/2007q3/000255.html).
A [2022 Sailfish community discussion](https://forum.sailfishos.org/t/update-gnupg-in-repos/12022)
attributes the older core-package baseline to GPLv3 distribution policy.
That is a historical community explanation, not a confirmed statement of
Jolla's current policy.

[pass with pass-otp](https://github.com/misja/sailfish-password-store) uses this runtime.

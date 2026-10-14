# Version and licensing background

The project SDK inventory recorded gnupg2 2.0.4+git6-1.8.4.jolla in the
SailfishOS-5.1.0.11-aarch64 target. That observation is scoped to the examined
SDK environment; a version label alone does not establish the patch content,
security status or package behavior of every Sailfish release.

Modern OpenPGP workflows motivated evaluating a separate GnuPG 2.5.24 runtime.
For example, [upstream introduced Curve25519 encryption in GnuPG 2.1.7](https://lists.gnupg.org/pipermail/gnupg-users/2015-August/054092.html).
The package recipes and source lock keep the selected versions explicit.

Licensing is part of the distribution context. [GnuPG 2.0.5 switched to GPLv3](https://lists.gnupg.org/pipermail/gnupg-announce/2007q3/000255.html).
A [2022 Sailfish community discussion](https://forum.sailfishos.org/t/update-gnupg-in-repos/12022)
attributes the older core-package baseline to GPLv3 distribution policy.
That is a historical community explanation, not a confirmed statement of
Jolla's current policy.

This project treats licensing and platform compatibility as normal distribution
requirements. Its isolated community runtime preserves the system stack while
making source, component licenses and package behavior reviewable. Replacing
Jolla packages is outside the private-runtime design.

A concrete integration goal is [pass with pass-otp](https://github.com/misja/sailfish-password-store)
for password and OTP storage using modern OpenPGP keys. Synthetic tests and a
limited development trial do not establish general migration or production
acceptance; follow the repository issues for remaining lifecycle and target work.

#!/usr/bin/env python3
"""Generate a same-payload release-bump RPM fixture; not a software upgrade."""
from pathlib import Path
root = Path('/home/ubuntu/gnupg-runtime')
base = (root / 'rpm/sailfish-gnupg-private.spec').read_text()
header = base.split('%prep', 1)[0].replace('Release: 0.1', 'Release: 0.2')
fixture = header + '''%install
mkdir -p %{buildroot}/usr/libexec %{buildroot}/usr/bin
cp -a /usr/libexec/sailfish-gnupg %{buildroot}/usr/libexec/
cp -a /usr/bin/sailfish-gpg %{buildroot}/usr/bin/

%files
%{private_prefix}
/usr/bin/sailfish-gpg
'''
(root / 'rpm/synthetic-upgrade.spec').write_text(fixture)
print('Prepared synthetic RPM release 0.2 fixture with unchanged installed payload')

# Standalone packaging of the upstream Sailfish Secrets pinentry component.
# Draft: dependency availability and final SDK/device RPM review remain gates.
Name:           pinentry-sailfish
Version:        0.2.44
Release:        0.1
Summary:        Sailfish OS native passphrase entry
License:        BSD-3-Clause AND LGPL-2.1-or-later
URL:            https://github.com/sailfishos/sailfish-secrets
Source0:        sailfish-secrets-0.2.44-5a8d33e2.tar.gz
Source1:        pinentry-sailfish.pro
Source2:        source-provenance.json
Source3:        libassuan-COPYING.LIB
Source4:        RELINK.md
Patch1:         0001-option-error-codes.patch
Patch2:         0002-assuan-api-compatibility.patch
Patch3:         0003-cache-hit-provenance.patch
Patch4:         0004-external-cache-permission.patch
Patch5:         0005-keyinfo-precedence.patch
BuildRequires:  qt5-qmake
BuildRequires:  pkgconfig(Qt5Core)
BuildRequires:  pkgconfig(Qt5DBus)
BuildRequires:  pkgconfig(sailfishsecrets)
BuildRequires:  pkgconfig(mlite5)
BuildRequires:  pkgconfig(gpg-error)
BuildRequires:  libassuan-devel
# The vendor bundle owns the same /usr/bin/pinentry. Do not replace its files
# or pretend that this UI component provides its OpenPGP/S/MIME crypto plugins.
Conflicts:      sailfishsecretsdaemon-cryptoplugins-gnupg

%description
Native passphrase-entry helper from Sailfish Secrets, using Sailfish system
interaction dialogs. This standalone package includes protocol compatibility
fixes for modern GnuPG and preserves the upstream binary name, pinentry.
It does not include the Sailfish OpenPGP or S/MIME crypto plugins.

%prep
%setup -q -n sailfish-secrets-0.2.44
%autopatch -p1
cp %{SOURCE1} plugins/gnupgplugin/pinentry/pinentry-sailfish.pro

%build
cd plugins/gnupgplugin/pinentry
qmake pinentry-sailfish.pro "CONFIG+=force_debug_info" "QMAKE_CXXFLAGS+=%{optflags}"
make %{?_smp_mflags}

%install
install -D -m 0755 plugins/gnupgplugin/pinentry/pinentry %{buildroot}%{_bindir}/pinentry
install -D -m 0644 LICENSE %{buildroot}%{_datadir}/licenses/%{name}/LICENSE
install -D -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/licenses/%{name}/libassuan-COPYING.LIB
install -D -m 0644 %{SOURCE4} %{buildroot}%{_docdir}/%{name}/RELINK.md
mkdir -p %{buildroot}%{_docdir}/%{name}/relink
cp plugins/gnupgplugin/pinentry/*.o %{buildroot}%{_docdir}/%{name}/relink/
install -D -m 0644 %{SOURCE2} %{buildroot}%{_docdir}/%{name}/source-provenance.json

%files
%{_bindir}/pinentry
%license %{_datadir}/licenses/%{name}
%doc %{_docdir}/%{name}

%global secretsdaemon sailfishsecretsdaemon
# Downstream plugin candidate: source rebuild preserves the reviewed target pins.
%global vendor_framework_release 1.14.3.jolla

Name:       sailfish-secrets
Summary:    Sailfish OS framework for secrets storage and cryptographic operations
Version:    0.2.44
Release:    1.14.3.jolla.compat3
License:    BSD
URL:        https://github.com/sailfishos/sailfish-secrets
Source0:    %{name}-%{version}.tar.bz2
Source10:   sailfish-secrets-LICENSE
Source11:   libassuan-COPYING.LIB
Source12:   NOTICE
Source13:   RELINK.md
Source14:   REBUILD.md
Patch1:     0001-option-error-codes.patch
Patch2:     0002-assuan-api-compatibility.patch
Patch3:     0003-cache-hit-provenance.patch
Patch4:     0004-external-cache-permission.patch
Patch5:     0005-keyinfo-precedence.patch
BuildRequires:  pkgconfig(Qt5Core)
BuildRequires:  pkgconfig(Qt5Sql)
BuildRequires:  pkgconfig(Qt5DBus)
BuildRequires:  pkgconfig(Qt5Gui)
BuildRequires:  pkgconfig(Qt5Qml)
BuildRequires:  pkgconfig(Qt5Quick)
BuildRequires:  pkgconfig(Qt5QuickTest)
BuildRequires:  pkgconfig(Qt5Concurrent)
BuildRequires:  pkgconfig(qt5-boostable)
BuildRequires:  qt5-qttools-qthelp-devel
BuildRequires:  qt5-tools
BuildRequires:  qt5-qttools-linguist
BuildRequires:  qt5-plugin-sqldriver-sqlite
BuildRequires:  pkgconfig(libcrypto)
BuildRequires:  pkgconfig(nemodevicelock)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(systemsettings)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  pkgconfig(sqlcipher)
BuildRequires:  pkgconfig(gpg-error)
BuildRequires:  pkgconfig(mlite5)
BuildRequires:  gpgme-devel
BuildRequires:  libassuan-devel
BuildRequires:  sailfish-qdoc-template

%description
%{summary}.

%package -n libsailfishsecrets
Summary:    Sailfish OS secrets storage system functionality client library

%description -n libsailfishsecrets
%{summary}.

%package -n libsailfishsecrets-devel
Summary:    Development package for Sailfish OS Secrets Library
Requires:   libsailfishsecrets = %{version}-%{release}

%description -n libsailfishsecrets-devel
%{summary}.

%package -n libsailfishsecrets-doc
Summary: Documentation for Sailfish OS Secrets Library

%description -n libsailfishsecrets-doc
%{summary}.

%package -n libsailfishsecrets-tests
Summary:    Unit tests for the Sailfish OS Secrets Library
Requires:   qt5-qtdeclarative-import-qttest
Requires:   qt5-qtdeclarative-devel-tools
Requires:   libsailfishsecrets = %{version}-%{release}
Requires:   nemo-qml-plugin-devicelock

%description -n libsailfishsecrets-tests
%{summary}.

%package   ts-devel
Summary:   Translation source for Sailfish Secrets

%description ts-devel

%package -n libsailfishsecretspluginapi
Summary:    Sailfish OS Secrets Library plugin abstract base classes
Requires:   libsailfishsecrets = %{version}-%{release}

%description -n libsailfishsecretspluginapi
%{summary}.

%package -n libsailfishsecretspluginapi-devel
Summary:    Sailfish OS Secrets Library plugin abstract base class development headers
Requires:   libsailfishsecrets = %{version}-%{release}
Requires:   libsailfishsecretspluginapi = %{version}-%{release}

%description -n libsailfishsecretspluginapi-devel
%{summary}.

%package -n libsailfishsecretsplugin
Summary:    QML plugin providing types for applications using libsailfishsecrets
Requires:   libsailfishsecrets = %{version}-%{release}

%description -n libsailfishsecretsplugin
%{summary}.

%package -n libsailfishcrypto
Summary:    Sailfish OS cryptographic operations system functionality client library

%description -n libsailfishcrypto
%{summary}.

%package -n libsailfishcrypto-devel
Summary:    Development package for Sailfish OS Crypto Library
Requires:   libsailfishcrypto = %{version}-%{release}

%description -n libsailfishcrypto-devel
%{summary}.

%package -n libsailfishcrypto-doc
Summary: Documentation for Sailfish OS Crypto Library

%description -n libsailfishcrypto-doc
%{summary}.

%package -n libsailfishcrypto-tests
Summary:    Unit tests for the libsailfishcrypto library
Requires:   libsailfishcrypto = %{version}-%{release}

%description -n libsailfishcrypto-tests
%{summary}.

%package -n libsailfishcryptopluginapi
Summary:    Sailfish OS Crypto Library plugin abstract base classes
Requires:   libsailfishsecrets = %{version}-%{release}
Requires:   libsailfishsecretspluginapi = %{version}-%{release}

%description -n libsailfishcryptopluginapi
%{summary}.

%package -n libsailfishcryptopluginapi-devel
Summary:    Sailfish OS Crypto Library plugin development headers
Requires:   libsailfishsecrets = %{version}-%{release}
Requires:   libsailfishcryptopluginapi = %{version}-%{release}
Requires:   libsailfishsecretspluginapi-devel = %{version}-%{release}

%description -n libsailfishcryptopluginapi-devel
%{summary}.

%package -n libsailfishcryptoplugin
Summary:    QML plugin providing types for applications using libsailfishcrypto
Requires:   libsailfishcrypto = %{version}-%{release}

%description -n libsailfishcryptoplugin
%{summary}.

%package -n libsailfishsecretscrypto
Summary:    Sailfish OS Secrets And Crypto C API library

%description -n libsailfishsecretscrypto
%{summary}.


%package -n libsailfishsecretscrypto-devel
Summary:    Development package for Sailfish OS Secrets And Crypto C API library
Requires:   libsailfishsecretscrypto = %{version}-%{release}

%description -n libsailfishsecretscrypto-devel
%{summary}.


%package -n libsailfishsecretscrypto-tests
Summary:    Unit tests for the libsailfishsecretscrypto library.
Requires:   libsailfishsecretscrypto = %{version}-%{release}

%description -n libsailfishsecretscrypto-tests
%{summary}.

%package -n %{secretsdaemon}
Summary:    Sailfish OS secrets daemon
Requires:         libsailfishsecrets = %{version}-%{release}
Requires:         systemd
%{?systemd_requires}
Requires:         mapplauncherd
Requires:         libsailfishcrypto = %{version}-%{release}
Requires:         qt5-plugin-sqldriver-sqlcipher
Requires:         nemo-qml-plugin-systemsettings

%description -n %{secretsdaemon}
Provides a secrets storage and cryptographic operations system daemon service,
which exposes functionality provided by libsailfishsecrets and libsailfishcrypto to clients via DBus.

%package -n %{secretsdaemon}-secretsplugins-default
Summary:    Sailfish OS secrets daemon plugins
Provides: %{secretsdaemon}-secretsplugins
Provides: %{secretsdaemon}-secretsplugin-ssl
Provides: %{secretsdaemon}-secretsplugin-sql
Requires:   qt5-plugin-sqldriver-sqlcipher
Requires:   libsailfishsecretspluginapi = %{version}-%{release}
Requires:   %{secretsdaemon} = %{version}-%{release}
Requires:   %{secretsdaemon}-secretsplugin-common = %{version}-%{release}

%description -n %{secretsdaemon}-secretsplugins-default
%{summary}.

%package -n %{secretsdaemon}-secretsplugin-common
Summary:    Sailfish OS secrets plugins that are mandatory for all platforms
Requires:  qt5-plugin-sqldriver-sqlite
Requires:  qt5-plugin-sqldriver-sqlcipher
Requires:  libsailfishsecretspluginapi = %{version}-%{release}
Requires:  %{secretsdaemon} = %{version}-%{release}
Requires:  nemo-qml-plugin-devicelock
Requires:  polkit >= 0.105+git3

%description -n %{secretsdaemon}-secretsplugin-common
%{summary}.

%package -n %{secretsdaemon}-cryptoplugins-default
Summary:    Sailfish OS crypto daemon plugins
Provides: %{secretsdaemon}-cryptoplugins
Provides: %{secretsdaemon}-cryptoplugin-ssl
Requires:   %{secretsdaemon} = %{version}-%{release}
Requires:   libsailfishcrypto = %{version}-%{release}
Requires:   libsailfishcryptopluginapi = %{version}-%{release}

%description -n %{secretsdaemon}-cryptoplugins-default
%{summary}.

%package -n %{secretsdaemon}-cryptoplugins-gnupg
License:    BSD-3-Clause AND LGPL-2.1-or-later
Summary:    Sailfish OS crypto daemon plugins for GnuPG
Requires:   %{secretsdaemon} = %{version}-%{vendor_framework_release}
Requires:   libsailfishcrypto = %{version}-%{vendor_framework_release}
Requires:   libsailfishcryptopluginapi = %{version}-%{vendor_framework_release}
Requires:   %{secretsdaemon}-secretsplugin-common

%description -n %{secretsdaemon}-cryptoplugins-gnupg
%{summary}.


%package -n sailfishsecrets-tool
Summary:    Command line tool to interact with the Sailfish OS Secrets and Crypto service
Requires:   libsailfishcrypto = %{version}-%{release}
Requires:   libsailfishsecrets = %{version}-%{release}

%description -n sailfishsecrets-tool
%{summary}.


%package -n qt5-plugin-sqldriver-sqlcipher
Summary:    QtSql driver plugin using SQLCipher

%description -n qt5-plugin-sqldriver-sqlcipher
%{summary}.


%prep
%setup -q -n %{name}-%{version}
%autopatch -p1

%build
%qmake5 "VERSION=%{version}"
%make_build

%install
rm -rf %{buildroot}
%qmake5_install

# Keep LGPL relink materials with the selected plugin, without new executables.
install -D -m 0644 %{SOURCE10} %{buildroot}%{_datadir}/licenses/%{secretsdaemon}-cryptoplugins-gnupg/sailfish-secrets-LICENSE
install -D -m 0644 %{SOURCE11} %{buildroot}%{_datadir}/licenses/%{secretsdaemon}-cryptoplugins-gnupg/libassuan-COPYING.LIB
install -D -m 0644 %{SOURCE12} %{buildroot}%{_docdir}/%{secretsdaemon}-cryptoplugins-gnupg/NOTICE
install -D -m 0644 %{SOURCE13} %{buildroot}%{_docdir}/%{secretsdaemon}-cryptoplugins-gnupg/RELINK.md
install -D -m 0644 %{SOURCE14} %{buildroot}%{_docdir}/%{secretsdaemon}-cryptoplugins-gnupg/REBUILD.md
mkdir -p %{buildroot}%{_docdir}/%{secretsdaemon}-cryptoplugins-gnupg/relink
for object in pinentry.o qassuanserver.o moc_qassuanserver.o; do
    install -m 0644 plugins/gnupgplugin/pinentry/$object %{buildroot}%{_docdir}/%{secretsdaemon}-cryptoplugins-gnupg/relink/$object
done

mkdir -p %{buildroot}/%{_docdir}/Sailfish/Secrets/
mkdir -p %{buildroot}/%{_docdir}/Sailfish/Crypto/
mkdir -p %{buildroot}%{_userunitdir}/user-session.target.wants/
mkdir -p %{buildroot}/%{_datadir}/dbus-1/services/
mkdir -p %{buildroot}/%{_datadir}/mapplauncherd/privileges.d/

cp -R lib/Secrets/doc/html/* %{buildroot}/%{_docdir}/Sailfish/Secrets/
cp -R lib/Crypto/doc/html/* %{buildroot}/%{_docdir}/Sailfish/Crypto/
install -m 0644 daemon/sailfish-secretsd.service %{buildroot}%{_userunitdir}
install -m 0644 daemon/sailfish-secretsd.privileges %{buildroot}/%{_datadir}/mapplauncherd/privileges.d/
install -m 0644 daemon/org.sailfishos.secrets.daemon.discovery.service %{buildroot}/%{_datadir}/dbus-1/services/

ln -s ../sailfish-secretsd.service %{buildroot}%{_userunitdir}/user-session.target.wants/sailfish-secretsd.service

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%post -n libsailfishsecrets -p /sbin/ldconfig

%postun -n libsailfishsecrets -p /sbin/ldconfig

%post -n libsailfishsecretspluginapi -p /sbin/ldconfig

%postun -n libsailfishsecretspluginapi -p /sbin/ldconfig

%post -n libsailfishcrypto -p /sbin/ldconfig

%postun -n libsailfishcrypto -p /sbin/ldconfig

%post -n libsailfishcryptopluginapi -p /sbin/ldconfig

%postun -n libsailfishcryptopluginapi -p /sbin/ldconfig

%post -n libsailfishsecretscrypto -p /sbin/ldconfig

%postun -n libsailfishsecretscrypto -p /sbin/ldconfig

%post -n libsailfishsecretsplugin -p /sbin/ldconfig

%postun -n libsailfishsecretsplugin -p /sbin/ldconfig

%post -n libsailfishcryptoplugin -p /sbin/ldconfig

%postun -n libsailfishcryptoplugin -p /sbin/ldconfig

%post -n %{secretsdaemon}
systemctl-user daemon-reload || :
systemctl-user reload-or-try-restart sailfish-secretsd || :

%preun -n %{secretsdaemon}
if [ "$1" -eq 0 ]; then
    systemctl stop sailfish-secretsd || :
fi

%postun -n %{secretsdaemon}
systemctl daemon-reload || :

%files -n libsailfishsecrets
%license LICENSE
%{_libdir}/libsailfishsecrets.so.*

%files -n libsailfishsecrets-devel
%{_libdir}/libsailfishsecrets.so
%{_libdir}/pkgconfig/sailfishsecrets.pc
%exclude %{_includedir}/Sailfish/Secrets/Plugins/extensionplugins.h
%{_includedir}/Sailfish/Secrets/*

%files -n libsailfishsecrets-doc
%{_docdir}/Sailfish/Secrets/*

%files -n libsailfishsecrets-tests
/opt/tests/Sailfish/Secrets/authentication-client
/opt/tests/Sailfish/Secrets/tst_secrets
/opt/tests/Sailfish/Secrets/tst_dataprotection
/opt/tests/Sailfish/Secrets/tst_secrets.qml
/opt/tests/Sailfish/Secrets/tst_secretsrequests
/opt/tests/Sailfish/Secrets/tst_secretsrequests.qml
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-testexampleusbtoken.so
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-testinappauth.so
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-testpasswordagentauth.so
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-testopenssl.so
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-testsqlcipher.so
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-testsqlite.so

%files ts-devel
%{_datadir}/translations/source/sailfish-secrets.ts

%files -n libsailfishsecretspluginapi
%{_libdir}/libsailfishsecretspluginapi.so.*

%files -n libsailfishsecretspluginapi-devel
%{_libdir}/libsailfishsecretspluginapi.so
%{_libdir}/pkgconfig/sailfishsecretspluginapi.pc
%{_includedir}/Sailfish/Secrets/Plugins/extensionplugins.h

%files -n libsailfishsecretsplugin
%{_libdir}/qt5/qml/Sailfish/Secrets/libsailfishsecretsplugin.so
%{_libdir}/qt5/qml/Sailfish/Secrets/qmldir
%{_libdir}/qt5/qml/Sailfish/Secrets/plugins.qmltypes
%{_libdir}/qt5/qml/Sailfish/Secrets/InteractionView.qml

%files -n libsailfishcrypto
%{_libdir}/libsailfishcrypto.so.*

%files -n libsailfishcrypto-devel
%{_libdir}/libsailfishcrypto.so
%{_libdir}/pkgconfig/sailfishcrypto.pc
%exclude %{_includedir}/Sailfish/Crypto/Plugins/extensionplugins.h
%{_includedir}/Sailfish/Crypto/*

%files -n libsailfishcrypto-doc
%{_docdir}/Sailfish/Crypto/*

%files -n libsailfishcrypto-tests
%{_bindir}/sailfishcryptoexample
%{_bindir}/sailfishcryptoqmlexample
/opt/tests/Sailfish/Crypto/tst_crypto
/opt/tests/Sailfish/Crypto/tst_cryptorequests
/opt/tests/Sailfish/Crypto/tst_cryptosecrets
/opt/tests/Sailfish/Crypto/tst_evp
/opt/tests/Sailfish/Crypto/tst_qml_signing
/opt/tests/Sailfish/Crypto/tst_qml_signing.qml
/opt/tests/Sailfish/Crypto/tst_qml_rsaencryptdecrypt
/opt/tests/Sailfish/Crypto/tst_qml_rsaencryptdecrypt.qml
/opt/tests/Sailfish/Crypto/tst_gnupgplugin
/opt/tests/Sailfish/Crypto/matrix/run-matrix-tests.sh
/opt/tests/Sailfish/Crypto/matrix/0*sh
%{_libdir}/Sailfish/Crypto/libsailfishcrypto-testopenssl.so
%{_libdir}/Sailfish/Crypto/libsailfishcrypto-testopenpgp.so

%files -n libsailfishcryptopluginapi
%{_libdir}/libsailfishcryptopluginapi.so.*

%files -n libsailfishcryptopluginapi-devel
%{_libdir}/libsailfishcryptopluginapi.so
%{_libdir}/pkgconfig/sailfishcryptopluginapi.pc
%{_includedir}/Sailfish/Crypto/Plugins/extensionplugins.h

%files -n libsailfishcryptoplugin
%{_libdir}/qt5/qml/Sailfish/Crypto/libsailfishcryptoplugin.so
%{_libdir}/qt5/qml/Sailfish/Crypto/qmldir
%{_libdir}/qt5/qml/Sailfish/Crypto/plugins.qmltypes

%files -n libsailfishsecretscrypto
%{_libdir}/libsailfishsecretscrypto.so.*

%files -n libsailfishsecretscrypto-devel
%{_libdir}/libsailfishsecretscrypto.so
%{_libdir}/pkgconfig/sailfishsecretscrypto.pc
%{_includedir}/Sailfish/SecretsCrypto/*

%files -n libsailfishsecretscrypto-tests
/opt/tests/Sailfish/SecretsCrypto/tst_secretscrypto

%files -n %{secretsdaemon}
%{_bindir}/sailfishsecretsd
%{_datadir}/translations/sailfish-secrets_eng_en.qm
%{_datadir}/mapplauncherd/privileges.d/sailfish-secretsd.privileges
%{_userunitdir}/sailfish-secretsd.service
%{_userunitdir}/user-session.target.wants/sailfish-secretsd.service
%{_datadir}/dbus-1/services/org.sailfishos.secrets.daemon.discovery.service

%files -n %{secretsdaemon}-secretsplugins-default
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-openssl.so
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-sqlite.so

%files -n %{secretsdaemon}-secretsplugin-common
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-inappauth.so
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-passwordagentauth.so
%{_libdir}/Sailfish/Secrets/libsailfishsecrets-sqlcipher.so
%{_datadir}/polkit-1/actions/org.sailfishos.secrets.policy

%files -n %{secretsdaemon}-cryptoplugins-default
%{_libdir}/Sailfish/Crypto/libsailfishcrypto-openssl.so

%files -n %{secretsdaemon}-cryptoplugins-gnupg
%license %{_datadir}/licenses/%{secretsdaemon}-cryptoplugins-gnupg/
%doc %{_docdir}/%{secretsdaemon}-cryptoplugins-gnupg/
%{_libdir}/Sailfish/Crypto/libsailfishcrypto-openpgp.so
%{_libdir}/Sailfish/Crypto/libsailfishcrypto-smime.so
%{_bindir}/pinentry

%files -n sailfishsecrets-tool
%{_bindir}/secrets-tool

%files -n qt5-plugin-sqldriver-sqlcipher
%{_libdir}/qt5/plugins/sqldrivers/libqsqlcipher.so
%changelog
* Wed Feb  4 2026 Pekka Vuorela <pekka.vuorela@jolla.com> - 0.2.44
- [sailfish-secrets] Migrate MGConfItem -> MDConfItem. JB#56217
* Thu Jan  8 2026 Pekka Vuorela <pekka.vuorela@jolla.com> - 0.2.43
- [sailfish-secrets] Avoid QScopedPointer::take() by std::unique_ptr. JB#63791
* Tue May 27 2025 Matti Lehtimäki <matti.lehtimaki@jolla.com> - 0.2.42
- [sailfish-secrets] Fix build with gcc 15. JB#63045
* Mon Jun 10 2024 Matti Lehtimäki <matti.lehtimaki@jolla.com> - 0.2.41
- [sailfish-secrets] Fix build with gcc 11 or newer. JB#62204
* Tue Apr 30 2024 Björn Bidar <bjorn.bidar@jolla.com> - 0.2.40
- [sailfish-secretscrypto] Ignore warning about deprecated OpenSSL functions for now. JB#55609
* Tue Apr 30 2024 Pekka Vuorela <pekka.vuorela@jollamobile.com> - 0.2.39
- [sailfish-secrets] Declare proper copy constructors for KeyPairGenerationParameters. JB#55609
* Wed Jan 24 2024 Matti Lehtimäki <matti.lehtimaki@jolla.com> - 0.2.38
- [sailfish-secrets] Use default copy assignment operator for KeyResult. JB#60722
- [sailfish-secrets] Use default copy assignment operator for KeyResult.JB#60722
* Wed Sep 20 2023 Pekka Vuorela <pekka.vuorela@jollamobile.com> - 0.2.37
- [readme] Update IRC info. JB#54410
- [sailfish-secrets] Don't show cache confirmation when dismissed.
- [sailfish-secrets] Properly detect the key ID in case of a subkey.
- [sailfish-secrets] Properly handle gpg sub id. Fixes JB#61127
* Wed Jan 25 2023 martyone <martin.kampas@jolla.com> - 0.2.36
- [sailfish-crypto] Add plugins.qmltypes. JB#59899
- [sailfish-secrets] Add plugins.qmltypes. JB#59899
* Tue Jan 24 2023 Ville Nummela <ville.nummela@jolla.com> - 0.2.35
- [sailfish-crypto] Use 0.2 as documentation version. JB#59768
- [sailfish-secrets] Use 0.2 as documentation version. JB#59768
* Thu Aug 18 2022 Ville Nummela <ville.nummela@jolla.com> - 0.2.34
- [sailfish-crypto] Add documentation for Sailfish.Crypto QML types. JB#58510
- [sailfish-crypto] Add QML documentation. JB#58510
- [sailfish-crypto] Fix VerifyRequest::verificationStatus() documentation
- [sailfish-crypto] Properly set project and url in qdocconf. JB#58510
- [sailfish-secrets] Add documentation for Sailfish.Secret QML types. JB#58510
- [sailfish-secrets] Add QML documentation. JB#58510
- [sailfish-secrets] Properly set project and url in qdocconf. JB#58510
* Thu Aug 11 2022 Ville Nummela <ville.nummela@jolla.com> - 0.2.33
- [sailfish-secrets] Give INCLUDEPATH in example. JB#58501
- [sailfish-secrets] Use correct include lines in documentation. JB#58501
* Fri Jan 14 2022 Pekka Vuorela <pekka.vuorela@jollamobile.com> - 0.2.32
- [sailfish-secrets] Indicate sqlcipher db v3 compatibility. JB#57036
- [sailfish-secrets] Indicate that SQLCipher db version is 3.
* Fri Dec 24 2021 Chris Adams <chris.adams@jolla.com> - 0.2.31
- [sailfish-secrets] Create the socket directory in the plugin also.
- [sailfish-secrets] Create the socket directory in the plugin also. Contributes to JB#56300
* Tue Dec  7 2021 Chris Adams <chris.adams@jolla.com> - 0.2.30
- [sailfish-secrets] Bump version. Contributes to JB#53600
* Tue Nov 23 2021 Chris Adams <chris.adams@jolla.com> - 0.2.28
- [sailfish-secrets] Correct p2p socket name for the password agent. Contributes to JB#56300
* Mon Nov 22 2021 Pekka Vuorela <pekka.vuorela@jollamobile.com> - 0.2.27
- [sailfish-secrets] Have license file as %%license. JB#55991
* Wed Nov 10 2021 Chris Adams <chris.adams@jolla.com> - 0.2.26
- [sailfish-secrets] Put the P2P DBus socket in a sub-directory of /run.
- [sailfish-secrets] Put the P2P DBus socket in a sub-directory of /run. Contributes to JB#56300
- [sailfish-secrets] Remove mentions of the Mailing list. Change references pointing to together.jolla.com to forum.sailfishos.org and rename all mentions of Together Jolla to Sailfish OS Forum. Contributes to: JB#53049
* Tue Nov  9 2021 blammit <bea.lam@jolla.com> - 0.2.25
- [SecretsCrypto] Update notification configuration. JB#50448
* Wed Nov  3 2021 Pekka Vuorela <pekka.vuorela@jollamobile.com> - 0.2.24
- [secrets] Adapt to sailfish-qdoc-template. JB#54004
* Wed Oct 13 2021 Björn Bidar <bjorn.bidar@jolla.com> - 0.2.23
- [packaging] BuildRequire systemd via pkgconfig. JB#55010
* Mon Oct  4 2021 Björn Bidar <bjorn.bidar@jolla.com> - 0.2.22
- [sailfish-secrets] Fix libgpg-error pkgconfig symbol name
- [sailfish-secrets] Fix libgpg-error pkgconfig symbol name. JB#55771
* Mon Nov  2 2020 Slava Monich <slava.monich@jolla.com> - 0.2.21
- [sailfish-secretscrypto] Don't depend on dbus-glib. Contributes to JB#51115
- [sailfish-secretscrypto] Fix gio/gunixfdlist.h not found
- [sailfishsecrets] Don't require shared libraries
* Fri Jun 12 2020 Matti Lehtimäki <matti.lehtimaki@gmail.com> - 0.2.20
- [aarch64] Use macros. Do not hardcode lib dir. Contributes to JB#50028
* Tue Apr 28 2020 Chris Adams <chris.adams@jollamobile.com> - 0.2.18
- [SecretsCrypto] Plug weak reference leak. Contributes to JB#44191
* Fri Jan 31 2020 Santtu Lakkala <santtu.lakkala@jolla.com> - 0.2.17
- [sailfish-secrets] Avoid wrong evaluation order of function arguments. Contributes to: JB#44191
- [sailfish-secretscrypto] Add in-app authentication test. Contributes to: JB#44191
- [sailfish-secretscrypto] Implement in-app authentication support. Contributes to: JB#44191
- [sailfish-secrets] Make inapp test plugin always use interaction service if defined. Contributes to: JB#44191
- [SecretsCrypto] Implement in-app authentication. Contributes to JB#44191
* Fri Jan 24 2020 Chris Adams <chris.adams@jollamobile.com> - 0.2.16
- [sailfish-secrets] Register types with appropriate meta type names. Contributes to JB#45215
* Mon Jan 20 2020 Marko Kenttälä <44089406+mkenttala@users.noreply.github.com> - 0.2.15
- [sailfish-secrets] Fix for hardcoded user. Fixes JB#47617
* Mon Jul 29 2019 martyone <martin.kampas@jolla.com> - 0.2.14
- [sailfish-secrets] Fix docs for C++ module indexes. Fixes JB#46721
* Tue Jul  2 2019 Chris Adams <chris.adams@jollamobile.com> - 0.2.13
- [daemon] Make platform application ID respect /etc/os-release. Contributes to JB#45838
- [daemon] Modify prompt text for user input. Contributes to JB#45838
* Fri Jun 28 2019 martyone <martin.kampas@jolla.com> - 0.2.12
- [sailfish-secrets] Improve documentation. Contributes to JB#46121
* Tue May 14 2019 Chris Adams <chris.adams@jollamobile.com> - 0.2.11
- [sailfish-secrets] Add a cancellation mechanism to authentication and user input requests.
- [sailfish-secrets] Add a cancellation mechanism to authentication and user input requests. Contributes to JB#45807
- [sailfish-secrets] Add disclaimer to documentation overview pages. Contributes to JB#45782
- [sailfish-secrets] Fix CollectionNamesRequest implementation
- [sailfish-secrets] Return an error to client on DBus connection error. Fix Github#155
* Tue Apr 16 2019 Chris Adams <chris.adams@jollamobile.com> - 0.2.10
- [sailfish-secrets] Ensure user input dialog timeout before request
- [sailfish-secrets] Ensure user input dialog timeout before request. Contributes to JB#44199
* Mon Mar  4 2019 Santtu Lakkala <santtu.lakkala@jolla.com> - 0.2.9
- [sailfish-secretscrypto] Cipher session implementation. Contributes to: JB#44188
- [sailfish-secrets] Ensure that authentication plugin are installed with GnuPG plugins.
* Fri Jan  4 2019 Raine Mäkeläinen <raine.makelainen@gmail.com> - 0.2.8
- [sailfish-secretscrypto] Add error domain quark getters. Contributes to: JB#44186
- [sailfish-secretscrypto] Add more tests. Contributes to: JB#44186
- [sailfish-secretscrypto] Use Secrets error domain for crypto storage errors. Contributes to JB#44186
* Wed Dec 19 2018 Chris Adams <chris.adams@jollamobile.com> - 0.2.7
- [sailfish-secrets] Don't fetch cache passphrase on retry.
- [sailfish-secrets] Don't fetch cache passphrase on retry. Contributes to JB#43783
- [sailfish-secrets] Remove QtGui linkage. Contributes to JB#36025
* Fri Dec 14 2018 Raine Mäkeläinen <raine.makelainen@gmail.com> - 0.2.6
- [sailfish-crypto] Fix compilation test openssl crypto plugin
- [sailfish-crypto] Fix TODO message in openssl crypto plugin
- [sailfish-crypto] Improve D-Bus serialization. Contributes to JB#42116
- [sailfish-secrets] Clean emails before storing them for S/MIME keys.
- [sailfish-secretscrypto] Add GObject API. Contributes to JB#42116
- [sailfish-secrets] Improve D-Bus serialization. Contributes to JB#42116
* Mon Nov 26 2018 Chris Adams <chris.adams@jollamobile.com> - 0.2.5
- [sailfish-secrets] Switch to password creation from operation(), and not from prompt texts. Contributes to JB#36797
* Fri Nov 23 2018 Chris Adams <chris.adams@jollamobile.com> - 0.2.4
- [sailfish-crypto] Rework Crypto unit tests. Contributes to JB#40058
- [sailfish-secrets] Add manual test instructions to README. Contributes to JB#42819
* Wed Nov 14 2018 Chris Adams <chris.adams@jollamobile.com> - 0.2.3
- [sailfish-secrets] Add a configuration key to store GnuPG passphrases.
- [sailfish-secrets] Add a new crypto plugin based on gpgme.
- [sailfish-secrets] Add a plugin to handle S/MIME certificates and crypto operations.
- [sailfish-secrets] Add a test file for GnuPG plugin.
- [sailfish-secrets] Add a .test plugin for OpenPGP one.
- [sailfish-secrets] Add support for key addition / removal in a collection for GnuPG keys.
- [sailfish-secrets] Allow to use file buffer for GPGme data source.
- [sailfish-secrets] Create a GnuPG pinentry based on the Secret API.
- [sailfish-secrets] Ensure that a password is provided on key generation.
- [sailfish-secrets] Export a logging category for plugins.
- [sailfish-secrets] Implement key finding based on capability.
- [sailfish-secrets] Update README with info about building GnuPG plugin. Contributes to JB#36797
* Fri Nov  9 2018 Chris Adams <chris.adams@jollamobile.com> - 0.2.2
- [sailfish-secrets] Call setFuture() in daemon after signal connection. Contributes to JB#36797
* Wed Oct 24 2018 Chris Adams <chris.adams@jollamobile.com> - 0.2.1
- [sailfish-secrets] Add parameters to the key generation QML bindings.
- [sailfish-secrets] Bump version. Contributes to JB#40058
- [sailfish-secrets] Export lists to QML from PluginInfoRequest.
* Wed Aug 29 2018 Timur Kristóf <venemo@msn.com> - 0.2.0
- [sailfish-secrets] Add a helper constructIdenifier() function to be able to set it in DeleteStoredKeyRequest and StoredKeyRequest from QML.
- [sailfish-secrets] Add a helper constructIdentifier() to be able to set the identifier in QML requests.
- [sailfish-secrets] Add health check request. Contributes to JB#42055
- [sailfish-secrets] Add health check to tool. Contributes to JB#42055
- [sailfish-secrets] Allow to create filterData for secrets.
- [sailfish-secrets] Better error messages. Contributes to JB#42055
- [sailfish-secrets] Data corruption notification. Contributes to JB#42055
- [sailfish-secrets] Deal with data corruption by deleting corrupted data for now. Contributes to JB#42055
- [sailfish-secrets] Declare the proper type for Secrets::Request::Status for QML.
- [sailfish-secrets] QML binding for HealthCheckRequest. Contributes to JB#42055
- [sailfish-secrets] Wrap the FindSecretsRequest to be able to list identifiers in QML.
* Tue Jul 17 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.23
- [sailfish-crypto] Fix failure in device lock authentication flow. Contributes to JB#40058
* Fri Jul  6 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.22
- [sailfish-secrets] Add ImportStoredKeyRequest in QML export.
- [sailfish-secrets] Fallback to devicelock API request if polkit fails. Contributes to JB#42295
- [sailfish-secrets] Fix crash in device lock authentication flow. Contributes to JB#42295
- [sailfish-secrets] Log additional information on metadata DB initialisation.
- [sailfish-secrets] Set full type for Request::Status for proper QML registration.
* Thu Jun 28 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.21
- [sailfish-secrets] Perform plugin name mapping. Contributes to JB#42192
* Tue Jun 19 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.20
- [sailfish-secrets] Allow dummy master lock key. Contributes to JB#42034
- [sailfish-secrets] Fix master lock key initialization. Contributes to JB#42034
* Wed Jun 13 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.19
- [sailfish-secrets] Add new GOST DigestFunction enum values.
- [sailfish-secrets] Add option to tool to request user input. Contributes to JB#42034
- [sailfish-secrets] Add support to pass custom parameters on CLI, fixes Github#122.
- [sailfish-secrets] Correct segfaults on exit in plugin cleanup code.
- [sailfish-secrets] Correct segfaults on exit in plugin cleanup code. Contributes to JB#36797
- [sailfish-secrets] Fallback to hardcoded p2p address on discovery failure. Contributes to JB#42034
- [sailfish-secrets] Improve application id determination. Contributes to JB#42038
* Mon May 28 2018 Timur Kristóf <venemo@msn.com> - 0.1.18
- [sailfish-secrets] Data protection for sensitive files. Fixes JB#41554
- [sailfish-secrets] Protect lock code data. Contributes to JB#41554
- [sailfish-secrets] Protect salt data. Contributes to JB#41554
* Fri May 25 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.17
- [sailfish-secrets] Enforce building with C++11 support. Contributes to JB#36797
- [sailfish-secrets] Initialize passwordagent once accepted. Contributes to JB#36797
- [sailfish-secrets] Report collection lock state from CollectionNamesRequest. Contributes to JB#36797
* Thu May 24 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.16
- [sailfish-crypto] Fix plugin API path issues. Contributes to JB#40058
* Tue May 22 2018 Raine Mäkeläinen <raine.makelainen@gmail.com> - 0.1.15
- [secrets] Fix rpmlint errors and reduce warnings. Contributes to JB#41938
* Tue May 22 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.14
- [sailfish-secrets] Add InteractionViewUserCanceledError error code. Contributes to JB#36797
* Tue May 22 2018 Raine Mäkeläinen <raine.makelainen@gmail.com> - 0.1.13
- [sailfish-secrets] Add support for keep-unlocked semantics to secrets-tool. Contributes to JB#36797
- [secrets] Align passphrase to lock code when applicable. Contributes to JB#36797
* Mon May 21 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.12
- [sailfish-crypto] Add import-stored-key support to test tool. Contributes to JB#41865
- [sailfish-crypto] Trigger collection unlock flow for crypto operations. Contributes to JB#40058
- [sailfish-secrets] Add QueryLockStatus operation to LockCodeRequest. Contributes to JB#36797
- [sailfish-secrets] Make PluginInfo read-only, fixes #90.
- [secrets] Change SecretsDaemonLocked error to IncorrectAuthenticationCode when unlocking master. Contributes to JB#41552
* Wed May 16 2018 Timur Kristóf <venemo@msn.com> - 0.1.11
- [secrets] Change SecretsDaemonLocked error to IncorrectAuthenticationCode when unlocking master. Contributes to JB#41552
- [secrets] Expose LockCodeRequest to qml. Contributes to JB#41552
* Tue May 15 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.10
- [sailfish-crypto] Add customParameters arg to StoredKey/StoredKeyIdentifiers. Contributes to JB#40058
- [sailfish-crypto] Rename some Result enum values. Contributes to JB#40058
- [sailfish-crypto] Use VerificationStatus instead of bool for verified values. Contributes to JB#40058
- [sailfish-secrets] Add missing hide_symbols to opensslcrypto in tests also.
- [sailfish-secrets] Add VerifyUser continuations for DeviceLocked data. Contributes to JB#36797
- [sailfish-secrets] Expand secrets tool to support DeviceLock semantics. Contributes to JB#36797
- [sailfish-secrets] Improve authentication plugin API. Contributes to JB#36797
- [sailfish-secrets] Improve readme. Contributes to JB#40058
- [sailfish-secrets] Make testopensslcrypto plugin to link with libcrypt.
- [sailfish-secrets] Use appropriate auth plugin depending on permissions. Contributes to JB#36797
- [sailfish-secrets] Use auth_self for VerifyUser polkit policy. Contributes to JB#36797
* Wed May  9 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.9
- [secrets] Split passphrase prompt text into multiple strings. Contributes to JB#40880
* Tue May  8 2018 Raine Mäkeläinen <raine.makelainen@gmail.com> - 0.1.8
- [sailfish-crypto] Implement Sign/Verify CipherRequest support. Contributes to JB#40058
- [sailfish-crypto] Update plugin documentation for changes in key importation routines.
- [sailfish-secrets] Expose PluginInfos to QML. Contributes to JB#41552
- [sailfish-secret] Update plugin documentation for changes in key importation routines.
* Thu May  3 2018 Timur Kristóf <venemo@msn.com> - 0.1.7
- [sailfish-crypto] Improve ImportKeyRequest API. Contributes to JB#40058
- [sailfish-secrets] Add default plugin packages that provides plugins. Contributes to JB#40058
- [sailfish-secrets] Add more status reporting API to PluginBase. Contributes to JB#41552
- [sailfish-secrets] Extend PluginInfo to expose more information. Contributes to JB#41552
* Thu May  3 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.6
- [sailfish-crypto] Add collectionName parameter to StoredKeyIdentifiersRequest. Contributes to JB#40058
- [sailfish-secrets] Add displayName() to PluginBase API. Contributes to JB#36797
* Wed May  2 2018 Timur Kristóf <venemo@msn.com> - 0.1.5
- [sailfish-secrets] Fix crash when opening signing again. Contributes to JB#40882
- [sailfish-secrets] Use QPointer in crypto and secrets managers. Contributes to JB#40882
* Tue May  1 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.4
- [sailfish-secrets] Add CCM support to Encrypt/DecryptRequest. Contributes to JB#40058
- [sailfish-secrets] Explicitly set IV and tag lengths for CipherRequests. Contributes to JB#40058
- [sailfish-secrets] Fix pre/post steps from daemon. Contributes to JB#40058
- [sailfish-secrets] Write documentation for plugin implementers. Contributes to JB#36797
* Thu Apr 26 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.3
- [sailfish-secrets] Add string translation ids. Contributes to JB#36797
- [sailfish-secrets] Fix for recent method renamings. Contributes to JB#40058
- [sailfish-secrets] Fix misspellings in the API. Contributes to JB#40058
- [sailfish-secrets] Fix stray comma. Contributes to JB#40058
- [sailfish-secrets] Fix warnings from QML. Contributes to JB#40058
- [sailfish-secrets] Use US spelling. Contributes to JB#40058
- [sailfish-secrets] Write command line tool. Contributes to JB#36797
* Thu Apr 19 2018 Chris Adams <chris.adams@jollamobile.com> - 0.1.2
- [sailfish-crypto] Implement example USB token for documentation purposes. Contributes to JB#40058
* Wed Apr 18 2018 Joona Petrell <joona.petrell@jollamobile.com> - 0.1.1
- [packaging] Fix broken dependencies. Contributes to JB#36797
* Wed Apr 18 2018 Joona Petrell <joona.petrell@jollamobile.com> - 0.1.0
- [packaging] Align source package naming to comply with Pootle requirements. Contributes to JB#36797
* Mon Apr 16 2018 Raine Mäkeläinen <raine.makelainen@gmail.com> - 0.0.9
- [packaging] Cleanup spec. Contributes to JB#36797
* Sun Apr 15 2018 Chris Adams <chris.adams@jollamobile.com> - 0.0.8
- [sailfish-crypto] Add custom parameters to Request. Contributes to JB#40058
- [sailfish-crypto] fix packaging issues with tests
- [sailfish-crypto] Perform crypto plugin operations in thread. Contributes to JB#40058
- [sailfish-secrets] don't build auth client without booster
- [sailfish-secrets] fix compilation with OpenSSL 1.1
- [sailfish-secrets] fix fallthrough
- [sailfish-secrets] fix warning in tst_cryptorequests
- [sailfish-secrets] Prevent bookkeeping database operation interleaving. Contributes to JB#36797
- [sailfish-secrets] Serialise plugin operations via QtConcurrent. Contributes to JB#36797
* Fri Apr 13 2018 Raine Mäkeläinen <raine.makelainen@gmail.com> - 0.0.7
- [sailfishsecrets] Start sailfish-secretsd upon boot. Fixes JB#41547
* Thu Apr 12 2018 Raine Makelainen <raine.makelainen@jolla.com> - 0.0.6
- [sailfish-secrets] Fix libcrypto linking to sqlcipherplugin and opensslplugin test plugins. Contributes to JB#41547
* Thu Apr 12 2018 Raine Makelainen <raine.makelainen@jolla.com> - 0.0.5
- [packaging] Fix build. Contributes to JB#36797
- [sailfish-crypto] add basic QML test for signing flow
- [sailfish-crypto] Add GCM support to DecryptRequest. Contributes to JB#40058
- [sailfish-crypto] Add GCM support to EncryptRequest. Contributes to JB#40058
- [sailfish-crypto] Add GenerateInitializationVectorRequest. Contributes to JB#40058
- [sailfish-crypto] add signatureLength to SignRequest contributes to JB#40058
- [sailfish-crypto] Add 'verified' value to indicate authenticated decryption result. Contributes to JB#40058
- [sailfish-crypto] fix key references with sign/verify in openssl plugin contributes to JB#40058
- [sailfish-crypto] fix up stuff in QML contributes to JB#40058
- [sailfish-crypto] Remove authenticatedEncrypt/Decrypt(). Contributes to JB#40058
- [sailfish-crypto] Rename 'tag' to 'authenticationTag' for clarity. Contributes to JB#40058
- [sailfish-crypto] Various fixes for encrypt/decrypt/iv changes. Contributes to JB#40058
- [sailfish-secrets] Add missing dependencies for QML tests.
- [sailfish-secrets] Add missing Qt5QuickTest dependencies and cleanup extras. Contributes to JB#36797
- [sailfish-secrets] fix issues with Secrets QML module contributes to JB#40882
- [sailfish-secrets] Fix libcrypto linking to sqlcipherplugin and opensslplugin. Contributes to JB#41547
- [sailfish-secrets] fix some packaging issues contributes to JB#40053
- [sailfish-secrets] Wrap StoredKeyIdentifiersRequest to be QML-friendly contributes to JB#40882
- [secrets] Add a lipstick password authentication plugin. Contributes to JB#40880
- [secrets] Add ImportKey and ImportStoredKey requests. Contributes to JB#41553
* Thu Apr 12 2018 Raine Mäkeläinen <raine.makelainen@gmail.com> - 0.0.4
- [sailfish-crypto] add basic QML test for signing flow
- [sailfish-crypto] Add GCM support to DecryptRequest. Contributes to JB#40058
- [sailfish-crypto] Add GCM support to EncryptRequest. Contributes to JB#40058
- [sailfish-crypto] Add GCM support to Encrypt/Request & DecryptRequest. Contributes to JB#40058
- [sailfish-crypto] Add GenerateInitializationVectorRequest. Contributes to JB#40058
- [sailfish-crypto] add signatureLength to SignRequest
- [sailfish-crypto] Add 'verified' value to indicate authenticated decryption result. Contributes to JB#40058
- [sailfish-crypto] fix key references with sign/verify in openssl plugin
- [sailfish-crypto] fix up stuff in QML
- [sailfish-crypto] Remove authenticatedEncrypt/Decrypt(). Contributes to JB#40058
- [sailfish-crypto] Rename 'tag' to 'authenticationTag' for clarity. Contributes to JB#40058
- [sailfish-crypto] Various fixes for encrypt/decrypt/iv changes. Contributes to JB#40058
- [sailfish-secrets] Add missing dependencies for QML tests.
- [sailfish-secrets] Add missing Qt5QuickTest dependencies and cleanup extras. Contributes to JB#36797
- [sailfish-secrets] fix issues with Secrets QML module
- [sailfish-secrets] Fix libcrypto linking to sqlcipherplugin and opensslplugin. Contributes to JB#41547
- [sailfish-secrets] fix some packaging issues
- [sailfish-secrets] Wrap StoredKeyIdentifiersRequest to be QML-friendly
- [secrets] Add a lipstick password authentication plugin. Contributes to JB#40880
- [secrets] Add ImportKey and ImportStoredKey requests. Contributes to JB#41553
* Thu Apr  5 2018 Raine Makelainen <raine.makelainen@jolla.com> - 0.0.3
- [sailfish-secrets] Update version. Contributes to JB#36797
* Wed Apr  4 2018 Timur Kristóf <venemo@msn.com> - 0.0.2
- [sailfish-crypto] add support for SHA-512 and MD5 with tests
- [sailfish-crypto] add support for some RSA paddings
- [sailfish-crypto] add test for sign+verify with EC key
- [sailfish-crypto] Carve out hard-coded AES
- [sailfish-crypto] EC key generation
- [sailfish-crypto] fix osslevp_key_is_rsa on OpenSSL < 1.1
- [sailfish-crypto] new style for evp.c
- [sailfish-crypto] Support for RSA encrypt/decrypt + tests
- [sailfish-secrets] refactor plugin load mechanism
* Tue Mar 27 2018 Chris Adams <chris.adams@jollamobile.com> - 0.0.1
- [sailfish-crypto] Add API for asymmetric cipher key pair generation. Contributes to JB#40058
- [sailfish-crypto] Add autotests for GCM mode (for AES encryption). Contributes to JB#40058
- [sailfish-crypto] Add CalculateDigestRequest. Contributes to JB#40058
- [sailfish-crypto] Add cipher session encrypt/decrypt support. Contributes to JB#40058
- [sailfish-crypto] Add CSPRNG functionality. Contributes to JB#40058
- [sailfish-crypto] Add support for AES encryption with ECB, CFB, OFB. Contributes to JB#40058
- [sailfish-crypto] Add support for CBC 128 and 192. Contributes to JB#40058
- [sailfish-crypto] Allow the client to limit retrieve key data. Contributes to JB#40058
- [sailfish-crypto] Allow user-defined data as input for KDF. Contributes to JB#40058
- [sailfish-crypto] Don't pad the cipher key. Contributes to JB#40058
- [sailfish-crypto] Expose LockCodeRequest in Crypto API. Contributes to JB#40058
- [sailfish-crypto] Fix bug in DeleteStoredKey request. Contributes to JB#40058
- [sailfish-crypto] Fix bugs in stored-crypto-key codepaths. Contributes to JB#40058
- [sailfish-crypto] Implement calculateDigest operation. Contributes to JB#40058
- [sailfish-crypto] Implement sign+verify support. Contributes to JB#40058
- [sailfish-crypto] Improve the encrypt/decrypt client API. Contributes to JB#40058
- [sailfish-crypto] Include explicit signature parameter to verify(). Contributes to JB#40058
- [sailfish-crypto] Make sqlcipher plugin a crypto+storage plugin. Contributes to JB#40058
- [sailfish-crypto] Only test GCM when testing CipherRequest. Contributes to JB#40058
- [sailfish-crypto] Remove deleteStoredSecret from Crypto plugin interface.  Contributes to JB#40058
- [sailfish-crypto] Remove duplicated evp_p.h. Contributes to JB#40058
- [sailfish-crypto] Remove explicit enum values that would be implicitly assigned
- [sailfish-crypto] Remove hardcoded references to block mode enum values
- [sailfish-crypto] remove included cpp file, contributes to JB#40058
- [sailfish-crypto] Remove unnecessary key hashing. Contributes to JB#40058
- [sailfish-crypto] Support AES with CTR and XTS. Contributes to JB#40058
- [sailfish-crypto] Support batch-mode Cipher requests. Contributes to JB#40058
- [sailfish-crypto] Test sign+verify against openssl commandline. Contributes to JB#40058
- [sailfish-crypto] Time-out inactive cipher sessions. Contributes to JB#40058
- [sailfish-crypto] Unify stored-crypto-key book-keeping. Contributes to JB#40058
- [sailfish-secrets] Add CollectionNamesRequest. Contributes to JB#36797
- [sailfish-secrets] Add framework overview documentation. Contributes to JB#36797
- [sailfish-secrets] Add SQLCipher-based EncryptedStoragePlugin. Contributes to JB#36797
- [sailfish-secrets] Add SQLCipher driver plugin for QtSql. Contributes to JB#36797
- [sailfish-secrets] Add support for InteractionRequest. Contributes to JB#36797
- [sailfish-secrets] Allow EncryptedStorage plugins to be Crypto plugins. Contributes to JB#36797
- [sailfish-secrets] Allow NoAccessControl semantic. Contributes to JB#36797
- [sailfish-secrets] Allow plugin-target lock code request. Contributes to JB#36797
- [sailfish-secrets] Allow user-requested data stored in secret. Contributes to JB#36797
- [sailfish-secrets] debug print database file, contributes to JB#40058
- [sailfish-secrets] Derive key from code for secrets encryption. Contributes to JB#36797
- [sailfish-secrets] Expose Secret type in top-level API. Contributes to JB#36797
- [sailfish-secrets] fix plugin load mechanism, contributes to JB#40058
- [sailfish-secrets] Implement and expose filtering operations. Contributes to JB#36797
- [sailfish-secrets] Implement master lock functionality. Contributes to JB#36797
- [sailfish-secrets] OpenSSL compiles on 1.1.0, contributes to JB#40058

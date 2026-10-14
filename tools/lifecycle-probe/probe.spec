%{!?probe_release:%global probe_release 1}
Name: sailfish-rpm-lifecycle-probe
Version: 1
Release: %{probe_release}
Summary: Disposable RPM scriptlet ordering probe
License: GPL-3.0-or-later
BuildArch: noarch
AutoReqProv: no
Requires: /bin/sh

%description
Inert disposable SDK-only probe. Contains no cryptography or personal data.

%prep
%build
%install
mkdir -p %{buildroot}/var/tmp/sailfish-rpm-lifecycle-probe
printf 'payload-%{release}\n' > %{buildroot}/var/tmp/sailfish-rpm-lifecycle-probe/payload

%pre
printf 'pre-%{release} existing=' >> /var/tmp/sailfish-rpm-lifecycle-probe.events
if test -f /var/tmp/sailfish-rpm-lifecycle-probe/payload; then
 cat /var/tmp/sailfish-rpm-lifecycle-probe/payload >> /var/tmp/sailfish-rpm-lifecycle-probe.events
else
 printf 'absent\n' >> /var/tmp/sailfish-rpm-lifecycle-probe.events
fi
%if %{probe_release} == 3
exit 1
%endif

%post
printf 'post-%{release} payload=' >> /var/tmp/sailfish-rpm-lifecycle-probe.events
cat /var/tmp/sailfish-rpm-lifecycle-probe/payload >> /var/tmp/sailfish-rpm-lifecycle-probe.events

%preun
printf 'preun-%{release} arg=%s payload=' "$1" >> /var/tmp/sailfish-rpm-lifecycle-probe.events
cat /var/tmp/sailfish-rpm-lifecycle-probe/payload >> /var/tmp/sailfish-rpm-lifecycle-probe.events

%postun
printf 'postun-%{release} arg=%s\n' "$1" >> /var/tmp/sailfish-rpm-lifecycle-probe.events

%files
/var/tmp/sailfish-rpm-lifecycle-probe

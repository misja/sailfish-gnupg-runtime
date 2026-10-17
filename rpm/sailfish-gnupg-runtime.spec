%global private_prefix /usr/libexec/sailfish-gnupg
%global __provides_exclude ^lib(assuan|gcrypt|gpg-error|ksba|npth)\\.so.*$
%global __requires_exclude ^lib(assuan|gcrypt|gpg-error|ksba|npth)\\.so.*$
Name: sailfish-gnupg-runtime
Version: 2.5.24
Release: 0.7
Summary: Modern GnuPG runtime alongside Sailfish OS system GnuPG
License: GPL-3.0-or-later AND LGPL-2.1-or-later AND LGPL-3.0-or-later
URL: https://gnupg.org/
Provides: sailfish-gnupg-private = %{version}-%{release}
Obsoletes: sailfish-gnupg-private < 2.5.24-0.7
Source0: sailfish-gnupg-runtime-%{version}.tar.gz
BuildRequires: chrpath
Requires(preun): /usr/bin/busybox
Requires: /usr/bin/busybox
Requires: /usr/bin/env
Requires: /usr/bin/getent
Requires: /usr/bin/id
Requires: (/bin/stat or /usr/bin/stat)

%description
GnuPG with separate commands, libraries, key directories and agents for
applications such as pass. Installs alongside Sailfish OS system GnuPG.

%prep
%setup -q -n sailfish-gnupg-runtime-%{version}
python3 tools/prepare-sources.py

%build
mkdir -p build
cd build
bash ../tools/build-runtime.sh "$(cd ../inspect && pwd)" "$(pwd)/stage"

%install
cp -a build/stage/. %{buildroot}/
test -x %{buildroot}%{private_prefix}/bin/gpg
for executable in %{buildroot}%{private_prefix}/bin/*; do
  case $(basename "$executable") in
    gpg|gpg-agent|gpgconf|gpg-connect-agent|pinentry|pinentry-tty|gpgv|gpgsplit|gpgtar) ;;
    *) rm -f "$executable" ;;
  esac
done
for executable in %{buildroot}%{private_prefix}/libexec/*; do
  case $(basename "$executable") in
    gpg-protect-tool) ;;
    *) rm -f "$executable" ;;
  esac
done
# Every private ELF's RUNPATH must contain only the final private library path.
for elf in $(find %{buildroot}%{private_prefix} -type f); do
  if readelf -h "$elf" >/dev/null 2>&1; then
    chrpath -c -r %{private_prefix}/lib "$elf"
  fi
done
mkdir -p %{buildroot}%{private_prefix}/licenses/project
install -m 0644 LICENSE LICENSING.md %{buildroot}%{private_prefix}/licenses/project/
for component in inspect/*; do
  name=$(basename "$component")
  mkdir -p "%{buildroot}%{private_prefix}/licenses/$name"
  for notice in "$component"/COPYING* "$component"/AUTHOR "$component"/AUTHORS "$component"/LICENSE*; do
    if test -e "$notice"; then
      cp -a "$notice" %{buildroot}%{private_prefix}/licenses/$name/
    fi
  done
done
find %{buildroot}%{private_prefix} -name '*.la' -delete
rm -rf %{buildroot}%{private_prefix}/include %{buildroot}%{private_prefix}/lib/pkgconfig
rm -f %{buildroot}%{private_prefix}/bin/gpgrt-config %{buildroot}%{private_prefix}/bin/gpg-error-config
mkdir -p %{buildroot}/usr/bin
install -m 0755 runtime/sailfish-gpg %{buildroot}/usr/bin/sailfish-gpg
install -m 0755 runtime/sailfish-gpg-agent %{buildroot}/usr/bin/sailfish-gpg-agent
install -m 0644 runtime/runtime-policy.sh %{buildroot}%{private_prefix}/libexec/runtime-policy.sh

%preun
# Ordinary final removal only. GnuPG handles startup and agent lifetime itself.
if [ "$1" -eq 0 ]; then
    private_prefix=%{private_prefix}
    # Refuse supported active clients before sending any shutdown request.
    for process in /proc/[0-9]*; do
        executable=$(/usr/bin/busybox readlink "$process/exe" 2>/dev/null) || continue
        case "$executable" in
            "$private_prefix/bin/gpg-agent"|"$private_prefix/bin/gpg-agent (deleted)") ;;
            "$private_prefix/bin/"*|"$private_prefix/libexec/"*)
                echo 'GnuPG is in use. Close the application and retry removal.' >&2
                exit 1 ;;
        esac
    done
    # A single TERM lets GnuPG request shutdown; repeated TERM can force exit.
    for process in /proc/[0-9]*; do
        executable=$(/usr/bin/busybox readlink "$process/exe" 2>/dev/null) || continue
        case "$executable" in
            "$private_prefix/bin/gpg-agent"|"$private_prefix/bin/gpg-agent (deleted)")
                test "$(/usr/bin/busybox readlink "$process/exe" 2>/dev/null)" = "$executable" || continue
                kill -TERM "${process##*/}" 2>/dev/null || \
                    echo 'Could not request private GnuPG agent shutdown.' >&2 ;;
        esac
    done
fi
exit 0

%files
%defattr(-,root,root,-)
%{private_prefix}
/usr/bin/sailfish-gpg
/usr/bin/sailfish-gpg-agent

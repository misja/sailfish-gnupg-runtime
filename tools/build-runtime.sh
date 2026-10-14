#!/bin/bash
set -euo pipefail
source_dir=$1
stage_root=$2
private_prefix=/usr/libexec/sailfish-gnupg
private_stage=$stage_root$private_prefix
mkdir -p "$private_stage"
export PATH="$private_stage/bin:$PATH"
export CPPFLAGS="-I$private_stage/include"
export LDFLAGS="-L$private_stage/lib -Wl,--enable-new-dtags,-rpath,$private_prefix/lib"
export PKG_CONFIG_PATH="$private_stage/lib/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="$stage_root"
# Build-local execution only; never set by installed wrappers.
export LD_LIBRARY_PATH="$private_stage/lib"
common=(--prefix="$private_prefix" --libdir="$private_prefix/lib" --disable-static)
build_one() {
  local component=$1
  shift
  local available_kib
  available_kib=$(df -Pk . | awk 'END {print $4}')
  if test "$available_kib" -lt 1048576; then
    echo 'Less than 1 GiB free: stopping before the next component' >&2
    exit 75
  fi
  echo "BUILDING $component"
  mkdir -p "$component-build"
  cd "$component-build"
  "$source_dir/$component/configure" "${common[@]}" "$@"
  make -j2
  make DESTDIR="$stage_root" install
  find "$private_stage/lib" -name '*.la' -exec sed -i "s|^libdir=.*|libdir='$private_stage/lib'|" {} +
  cd ..
}
build_one libgpg-error-1.61 --disable-doc
export GPGRT_CONFIG="$private_stage/bin/gpgrt-config"
build_one libgcrypt-1.12.4 --disable-doc --with-libgpg-error-prefix="$private_stage"
build_one libassuan-3.0.2 --disable-doc --with-libgpg-error-prefix="$private_stage"
build_one npth-1.8
build_one libksba-1.8.1 --disable-doc --with-libgpg-error-prefix="$private_stage"
build_one pinentry-1.3.3 --disable-doc --enable-pinentry-tty --disable-pinentry-curses --disable-fallback-curses --disable-pinentry-gtk2 --disable-pinentry-gnome3 --disable-pinentry-qt --disable-pinentry-qt4 --disable-pinentry-qt5 --disable-pinentry-tqt --disable-pinentry-fltk --disable-pinentry-efl --disable-libsecret --disable-inside-emacs --with-libassuan-prefix="$private_stage" --with-libgpg-error-prefix="$private_stage"
build_one gnupg-2.5.24 --disable-doc --disable-gpgsm --disable-scdaemon --disable-dirmngr --disable-keyboxd --disable-tpm2d --disable-wks-tools --disable-ldap --disable-tofu --disable-card-support --without-readline --with-libgpg-error-prefix="$private_stage" --with-libgcrypt-prefix="$private_stage" --with-libassuan-prefix="$private_stage" --with-ksba-prefix="$private_stage" --with-npth-prefix="$private_stage" --with-agent-pgm="$private_prefix/bin/gpg-agent" --with-pinentry-pgm="$private_prefix/bin/pinentry-tty"

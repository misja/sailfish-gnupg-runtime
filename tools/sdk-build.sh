#!/usr/bin/env bash
# Build using an explicitly selected installed SDK/target; no dependency install.
set -euo pipefail
project_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
sdk_root=${SAILFISH_SDK_ROOT:-"$HOME/SailfishOS"}
: "${SAILFISH_SDK_TARGET:?Set the exact reviewed installed SDK build target}"
test -x "$sdk_root/bin/sfdk" || {
  echo 'Set SAILFISH_SDK_ROOT to an installed SDK directory' >&2; exit 1;
}
cd "$project_dir"
test -f evidence/source-verification.json || {
  echo 'First authenticate sources with the sibling workspace tools/fetch-sources.py' >&2; exit 1;
}
mkdir -p evidence
"$sdk_root/bin/sfdk" -c "target=$SAILFISH_SDK_TARGET" \
  -c specfile=rpm/sailfish-gnupg-private.spec -c package.timeline \
  -c no-pull-build-requires -c no-vcs-apply build --prepare \
  2>&1 | tee evidence/latest-build.log

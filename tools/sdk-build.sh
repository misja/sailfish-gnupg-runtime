#!/usr/bin/env bash
# Inside the approved LXC project; builds the available feasibility target.
set -euo pipefail
project_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
test "$project_dir" = /home/ubuntu/gnupg-runtime || {
  echo 'Run inside sailfish-sdk, not on the host' >&2; exit 1;
}
cd "$project_dir"
test -f evidence/source-verification.json || {
  echo 'First run python3 tools/fetch-sources.py' >&2; exit 1;
}
# Override only after selecting and validating another installed SDK target.
sdk_target=${SAILFISH_SDK_TARGET:-SailfishOS-5.1.0.11-aarch64}
mkdir -p evidence
/home/ubuntu/SailfishOS/bin/sfdk -c "target=$sdk_target" \
  -c specfile=rpm/sailfish-gnupg-private.spec -c package.timeline \
  -c no-pull-build-requires -c no-vcs-apply build --prepare \
  2>&1 | tee evidence/latest-build.log

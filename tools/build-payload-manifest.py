#!/usr/bin/env python3
"""Generate the public installed-file manifest after RPM payload postprocessing."""
import argparse
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from lifecycle_control import Payload

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('buildroot', type=Path)
args = parser.parse_args()
root = args.buildroot
if not root.is_absolute() or root.resolve(strict=True) != root or root == Path('/'):
    raise SystemExit('Expected a canonical separate buildroot')
prefix = root / 'usr/libexec/sailfish-gnupg'
entrypoints = tuple(root / 'usr/bin' / name for name in ('sailfish-gpg', 'sailfish-gpg-agent'))
print('Payload generation:', Payload(prefix, entrypoints=entrypoints, expected_uid=os.geteuid()).build_manifest())

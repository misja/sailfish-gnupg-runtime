#!/usr/bin/env python3
"""Inspect installed private objects and stock coexistence in the SDK only."""
import json
import os
from pathlib import Path
import re
import subprocess

prefix = Path('/usr/libexec/sailfish-gnupg')
expected = str(prefix / 'lib')
environment = dict(os.environ)
environment.pop('LD_LIBRARY_PATH', None)
environment.pop('LD_PRELOAD', None)
def run(args):
    return subprocess.check_output(args, text=True, env=environment)
records = []
for path in sorted(prefix.rglob('*')):
    if path.is_symlink() or not path.is_file():
        continue
    with path.open('rb') as stream:
        if stream.read(4) != b'\x7fELF':
            continue
    header = run(['readelf', '-h', str(path)])
    dynamic = run(['readelf', '-d', str(path)])
    assert 'AArch64' in header, str(path)
    paths = re.findall(r'\((?:RUNPATH|RPATH)\).*\[(.*?)\]', dynamic)
    assert paths == [expected], (str(path), paths)
    needed = re.findall(r'\(NEEDED\).*\[(.*?)\]', dynamic)
    loaded = run(['/lib/ld-linux-aarch64.so.1', '--list', str(path)])
    for name in needed:
        if re.match(r'lib(?:gcrypt|gpg-error|assuan|ksba|npth)\.so', name):
            assert f'=> {expected}/{name}' in loaded, (str(path), name, loaded)
    records.append({'path': str(path), 'needed': needed, 'runpath': paths, 'loader': loaded})
assert records, 'No private ELF objects inspected'
output = Path('/home/ubuntu/gnupg-runtime/evidence/elf-runtime.json')
output.write_text(json.dumps(records, indent=2) + '\n')
print(f'PASS {len(records)} private aarch64 ELF objects: final loading paths and private dependency resolution')

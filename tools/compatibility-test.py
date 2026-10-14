#!/usr/bin/env python3
"""Run outside SDK target, inside LXC: existing distro GPG, public fixture only."""
import json
from pathlib import Path
import subprocess
import tempfile

root = Path('/home/ubuntu/gnupg-runtime')
test = json.loads((root / 'test-results/runtime-test.json').read_text())
source = Path(test['home'])
assert source.parent == root / 'test-results' and source.name.startswith('synthetic-')
home = Path(tempfile.mkdtemp(prefix='compat-public-', dir=root / 'test-results'))
gpg = ['gpg', '--no-options', '--homedir', str(home), '--batch']
def run(args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)
record = {'home': str(home), 'version': run(gpg + ['--version'])}
record['import'] = run(gpg + ['--import', str(source / 'public.asc')])
record['signature_verification'] = run(gpg + ['--verify', str(source / 'payload.sig'), str(source / 'payload.txt')])
fingerprint = next(line.split(':')[9] for line in run(gpg + ['--with-colons', '--list-keys']).splitlines() if line.startswith('fpr:'))
run(gpg + ['--trust-model', 'always', '--recipient', fingerprint, '--output', str(home / 'encrypted.gpg'), '--encrypt', str(source / 'payload.txt')])
(root / 'evidence/compatibility.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS existing LXC distro GPG verifies private runtime signature and encrypts to synthetic public key')

#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess

root = Path('/home/ubuntu/gnupg-runtime')
fixture = json.loads((root / 'test-results/runtime-test.json').read_text())
record = json.loads((root / 'evidence/compatibility.json').read_text())
source = Path(fixture['home'])
compat = Path(record['home'])
assert source.parent == compat.parent == root / 'test-results'
assert source.name.startswith('synthetic-') and compat.name.startswith('compat-public-')
result = subprocess.run(['/usr/bin/sailfish-gpg', '--batch', '--pinentry-mode', 'loopback', '--passphrase-fd', '0', '--decrypt', str(compat / 'encrypted.gpg')], input='NOT-A-REAL-SECRET-sdk-feasibility\n', text=True, capture_output=True, env=dict(os.environ, SAILFISH_GNUPGHOME=str(source)), timeout=120)
assert result.returncode == 0, result.stderr
assert result.stdout == (source / 'payload.txt').read_text()
record['private_runtime_decryption'] = 'passed: plaintext matches synthetic fixture'
(root / 'evidence/compatibility.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS private runtime decrypts existing distro GPG ciphertext')

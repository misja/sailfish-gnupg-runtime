#!/usr/bin/env python3
"""Summarize executed snapshot evidence; does not itself run lifecycle steps."""
import json
from pathlib import Path

root = Path('/home/ubuntu/gnupg-runtime')
baseline = json.loads((root / 'evidence/stock-before.json').read_text())
for phase in ['installed', 'upgraded', 'removed']:
    assert json.loads((root / f'evidence/stock-{phase}.json').read_text()) == baseline, phase
fixture = json.loads((root / 'test-results/runtime-test.json').read_text())
home = Path(fixture['home'])
assert home.parent == root / 'test-results' and home.name.startswith('synthetic-')
assert len(list((home / 'private-keys-v1.d').glob('*.key'))) == 2
record = {'stock_files_unchanged': len(baseline['files']), 'stock_package_versions_and_verification_unchanged': True, 'phases': ['install 0.1', 'same-payload RPM release upgrade 0.1 to 0.2', 'remove 0.2'], 'synthetic_keys_retained_after_removal': 2, 'upgrade_scope': 'same payload; software-version changes and key-format migrations not tested'}
(root / 'evidence/lifecycle.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS recorded lifecycle evidence and two retained synthetic private keys')

#!/usr/bin/env python3
"""Stop only agents belonging to this project's generated synthetic homes."""
import json
import os
from pathlib import Path
import subprocess

root = Path('/home/ubuntu/gnupg-runtime')
binary = root / 'build/gnupg-2.5.24-build/tools/gpg-connect-agent'
environment = dict(os.environ)
# Only this command's build-local loader environment; never installed globally.
environment['LD_LIBRARY_PATH'] = str(root / 'build/stage/usr/libexec/sailfish-gnupg/lib')
records = []
for home in sorted((root / 'test-results').glob('synthetic-*')):
    assert home.parent == root / 'test-results'
    if home.is_symlink() or not (home / 'S.gpg-agent').is_socket():
        continue
    result = subprocess.run([str(binary), '--homedir', str(home), '--no-autostart', 'KILLAGENT', '/bye'], text=True, capture_output=True, env=dict(environment, GNUPGHOME=str(home)), timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr)
    records.append({'home': str(home), 'result': result.stdout})
(root / 'evidence/agent-cleanup.json').write_text(json.dumps(records, indent=2) + '\n')
print(f'Stopped {len(records)} remaining synthetic fixture agents; no default home queried')

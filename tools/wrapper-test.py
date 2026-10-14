#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path('/home/ubuntu/gnupg-runtime')
record = json.loads((root / 'test-results/runtime-test.json').read_text())
home = record['home']
environment = dict(os.environ)
environment.pop('SAILFISH_GNUPGHOME', None)
def rejected(args, env):
    result = subprocess.run(['/usr/bin/sailfish-gpg'] + args, env=env, capture_output=True)
    assert result.returncode == 64, (args, result.returncode)
rejected(['--version'], environment)
environment['SAILFISH_GNUPGHOME'] = home
for arguments in [['--homedir', '/tmp'], ['--homed=/tmp'], ['--opt', '/tmp'], ['--agent-p', '/tmp']]:
    rejected(arguments, environment)
unsafe = Path(tempfile.mkdtemp(prefix='synthetic-permissions-', dir=root / 'test-results'))
unsafe.chmod(0o755)
rejected(['--version'], dict(environment, SAILFISH_GNUPGHOME=str(unsafe)))
result = subprocess.run(['/usr/bin/sailfish-gpg','--version'], env=environment, capture_output=True, text=True)
assert result.returncode == 0 and '2.5.24' in result.stdout
(root / 'evidence/wrapper-test.json').write_text(json.dumps({'missing_home':'rejected', 'unsafe_mode':'rejected', 'home_and_helper_overrides':'rejected including abbreviations', 'valid_home_version':'passed'}, indent=2) + '\n')
print('PASS explicit-home/permission guards and override rejection')

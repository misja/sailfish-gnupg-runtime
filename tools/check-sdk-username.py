#!/usr/bin/env python3
"""Run upstream tests with a temporary SDK-only account fixture; restore bytes."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/ubuntu/gnupg-runtime')
if Path.cwd() != ROOT:
    raise SystemExit('Run only in the approved container project')
ENGINE = 'sailfish-sdk-build-engine_ubuntu'
TARGET = 'SailfishOS-5.1.0.11-aarch64'
ACCOUNT = f'/srv/mer/targets/{TARGET}.default/etc/passwd'

def docker(*args, data=None):
    return subprocess.run(['docker', 'exec', '-i', '--user', 'root', ENGINE, *args],
                          input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True).stdout

original = docker('cat', ACCOUNT)
if any(line.split(b':')[2:3] == [b'1000'] or line.startswith(b'mersdk:')
       for line in original.splitlines()):
    raise SystemExit('Unexpected existing account; refusing to change it')
fixture = b'mersdk:x:1000:100000:SDK test fixture:/home/mersdk:/sbin/nologin\n'
record = {'target': TARGET, 'uid': 1000, 'gid': 100000,
          'fixture_name': 'mersdk', 'original_sha256': hashlib.sha256(original).hexdigest()}
evidence = ROOT / 'evidence'
evidence.mkdir(exist_ok=True)
try:
    docker('tee', ACCOUNT, data=original.rstrip(b'\n') + b'\n' + fixture)
    command = ['/home/ubuntu/SailfishOS/bin/sfdk', '-c', f'target={TARGET}',
               'build-shell', 'sh', '-c',
               'id; getent passwd 1000 && make -j2 -C build/libgpg-error-1.61-build check']
    with (evidence / 'libgpg-error-username-fixture-check.log').open('wb') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    record['test_exit_code'] = result.returncode
finally:
    docker('tee', ACCOUNT, data=original)
    restored = docker('cat', ACCOUNT)
    record['restored_sha256'] = hashlib.sha256(restored).hexdigest()
    record['restored_exactly'] = restored == original
    (evidence / 'sdk-username-fixture.json').write_text(json.dumps(record, indent=2) + '\n')
    if restored != original:
        raise SystemExit('Account restoration mismatch')
print(json.dumps(record, indent=2))
raise SystemExit(record.get('test_exit_code', 1))

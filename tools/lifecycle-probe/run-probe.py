#!/usr/bin/python3
"""SDK-only inert RPM probe. Explicit scoped install/remove approval required."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('rpm_directory', type=Path)
parser.add_argument('--approved-sdk-probe', action='store_true')
args = parser.parse_args()
assert args.approved_sdk_probe and os.getuid() == 0
# The available SDK target is 5.1, distinct from the upgraded phone target.
os_release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
assert os_release.get('ID', '').strip('"') == 'sailfishos'
assert os_release.get('VERSION_ID', '').strip('"') == '5.1.0.11'
env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}
name = 'sailfish-rpm-lifecycle-probe'
payload_dir = Path('/var/tmp/' + name)
events = Path('/var/tmp/' + name + '.events')
assert not payload_dir.exists() and not payload_dir.is_symlink()
assert not events.exists() and not events.is_symlink()
query = subprocess.run(['/usr/bin/rpm', '-q', name], env=env, capture_output=True)
assert query.returncode == 1
rpms = [args.rpm_directory / f'{name}-1-{r}.noarch.rpm' for r in (1, 2, 3)]
assert all(p.is_file() and not p.is_symlink() for p in rpms)
expected_hashes = {'sailfish-rpm-lifecycle-probe-1-2.noarch.rpm': '5392a4f2a72a438388a9cf7b1c0a54960ae1626c7134bc129fd3363508eff3e3', 'sailfish-rpm-lifecycle-probe-1-3.noarch.rpm': '52c16a7f3cc5b72e4d3d395fda14dbfff82383bb803bb4ba58b08c4684854bc5', 'sailfish-rpm-lifecycle-probe-1-1.noarch.rpm': 'ef5ee4f50f1d72196d036003b0f3258c7dc1787af6d2152208d88c08bb3e853a'}
assert all(hashlib.sha256(p.read_bytes()).hexdigest() == expected_hashes[p.name] for p in rpms)
records = Path(tempfile.mkdtemp(prefix='sailfish-rpm-probe-records-', dir='/home/ubuntu/gnupg-runtime'))
result = {'scope': 'Disposable SDK RPM ordering only; not device/lifecycle acceptance',
          'rpms': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in rpms},
          'stages': []}

def run(label, argv, expected=0):
    p = subprocess.run(['/usr/bin/rpm'] + argv, env=env, capture_output=True, timeout=90)
    (records / (label + '.stdout')).write_bytes(p.stdout)
    (records / (label + '.stderr')).write_bytes(p.stderr)
    result['stages'].append({'label': label, 'exitcode': p.returncode})
    assert p.returncode == expected, (label, p.returncode)
    return p.stdout

try:
    baseline = run('inventory-before', ['-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n'])
    run('test-install', ['-ivh', '--test', str(rpms[0])])
    assert not events.exists() and not payload_dir.exists()
    run('absent-after-test-install', ['-q', name], expected=1)
    after_test = run('inventory-after-test-install', ['-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n'])
    assert sorted(after_test.splitlines()) == sorted(baseline.splitlines())
    run('install', ['-ivh', str(rpms[0])])
    assert (payload_dir / 'payload').read_text() == 'payload-1\n'
    old_events = events.read_bytes()
    installed_inventory = run('inventory-installed', ['-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n'])
    run('test-upgrade', ['-Uvh', '--test', str(rpms[1])])
    assert events.read_bytes() == old_events
    assert (payload_dir / 'payload').read_text() == 'payload-1\n'
    assert run('version-after-test-upgrade', ['-q', '--qf', '%{RELEASE}\n', name]) == b'1\n'
    test_inventory = run('inventory-after-test-upgrade', ['-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n'])
    assert sorted(test_inventory.splitlines()) == sorted(installed_inventory.splitlines())
    run('upgrade', ['-Uvh', str(rpms[1])])
    assert (payload_dir / 'payload').read_text() == 'payload-2\n'
    assert 'preun-1 arg=1 payload=payload-2\n' in events.read_text()
    run('failed-upgrade', ['-Uvh', str(rpms[2])], expected=1)
    assert run('installed-after-failure', ['-q', '--qf', '%{RELEASE}\n', name]) == b'2\n'
    assert (payload_dir / 'payload').read_text() == 'payload-2\n'
    run('erase', ['-e', name])
    assert not payload_dir.exists()
    final = run('inventory-final', ['-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n'])
    assert sorted(baseline.splitlines()) == sorted(final.splitlines())
    (records / 'events.txt').write_bytes(events.read_bytes())
    assert events.is_file() and not events.is_symlink() and events.stat().st_uid == 0
    events.unlink()
    result['passed'] = True
except Exception as e:
    result['passed'] = False
    result['failure'] = str(e)
    # Retain uncertain state; never force removal or wipe a broad directory.
    raise
finally:
    (records / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Records:', records, flush=True)

#!/usr/bin/env python3
"""Observe own watchdog lifecycle with inert host stubs; never start GnuPG.

The observer owns a separate process group for each case and always removes it.
Only a temporary policy copy has its 15-second timer shortened to one second.
An interrupted owner is a boundary measurement, not a required passing cleanup.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source = Path(__file__).resolve().parents[1] / 'runtime/runtime-policy.sh'
text = source.read_text()
needle = '/usr/bin/busybox sleep 15 &'
assert text.count(needle) == 1
record = {'scope': 'host-only synthetic IPC lifecycle; no crypto/device acceptance',
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'timer_substitution': '15 seconds -> 1 second in temporary copy only',
          'cases': []}

def alive(pid):
    try:
        content = Path(f'/proc/{pid}/stat').read_text()
        return content.rsplit(') ', 1)[1].split()[0] != 'Z'
    except FileNotFoundError:
        return False

with tempfile.TemporaryDirectory(prefix='synthetic-watchdog-lifecycle-', dir='/tmp') as directory:
    root = Path(directory)
    policy = root / 'policy.sh'
    policy.write_text(text.replace(needle, '/usr/bin/busybox sleep 1 &'))
    owner = root / 'owner.sh'
    owner.write_text('set -eu\n. "$1"\nruntime_timed "$2"\n')
    for name, interrupt in [('owner_alive', None), ('owner_TERM', signal.SIGTERM),
                            ('owner_KILL', signal.SIGKILL)]:
        marker = root / f'{name}.pid'
        helper = root / f'{name}.sh'
        helper.write_text(f'#!/usr/bin/busybox sh\ntrap "" TERM\nprintf "%s\\n" "$$" > "{marker}"\nexec /usr/bin/busybox sleep 30\n')
        helper.chmod(0o700)
        env = {'PATH': '/usr/bin:/bin', 'SAILFISH_GNUPGHOME': directory,
               'HOME': directory, 'LC_ALL': 'C'}
        with (root / f'{name}.log').open('w') as log:
            process = subprocess.Popen(['/usr/bin/busybox', 'sh', str(owner), str(policy), str(helper)],
                                       env=env, stdout=log, stderr=log, start_new_session=True)
            child = None
            try:
                deadline = time.monotonic() + 5
                while not marker.exists():
                    assert process.poll() is None and time.monotonic() < deadline
                    time.sleep(0.05)
                child = int(marker.read_text())
                # Allow the watchdog to capture the original parent/start identity.
                time.sleep(0.2)
                if interrupt is not None:
                    process.send_signal(interrupt)
                    process.wait(timeout=3)
                else:
                    process.wait(timeout=6)
                time.sleep(2.5 if interrupt is not None else 0.1)
                survived = alive(child)
                if interrupt is None:
                    assert not survived and process.returncode != 0, 'Live-owner watchdog did not terminate inert IPC'
                record['cases'].append({'case': name, 'owner_exitcode': process.returncode,
                                        'ipc_alive_after_observation': survived,
                                        'wrapper_cleanup_established': not survived,
                                        'observer_cleanup': False})
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=3)
                if child is not None:
                    deadline = time.monotonic() + 3
                    while alive(child) and time.monotonic() < deadline:
                        time.sleep(0.05)
                    assert not alive(child), 'Own inert IPC survived observer process-group cleanup'
                if record['cases'] and record['cases'][-1]['case'] == name:
                    record['cases'][-1]['observer_cleanup'] = True

record['interrupted_owner_cleanup_proven'] = all(
    case['wrapper_cleanup_established'] for case in record['cases'])
args.output.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))

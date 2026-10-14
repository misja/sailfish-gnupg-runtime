#!/usr/bin/env python3
"""Synthetic SDK-only functional tests; never reads a normal GnuPG home."""
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import tempfile
import time

project = Path('/home/ubuntu/gnupg-runtime')
prefix = Path('/usr/libexec/sailfish-gnupg')
output = project / 'test-results'
output.mkdir(exist_ok=True)
home = Path(tempfile.mkdtemp(prefix='synthetic-', dir=output))
(home / 'gpg-agent.conf').write_text('log-file ' + str(home / 'agent.log') + '\nverbose\ndebug ipc\ndebug-pinentry\ndisable-scdaemon\n')
phrase = 'NOT-A-REAL-SECRET-sdk-feasibility'
env = dict(os.environ, SAILFISH_GNUPGHOME=str(home), GNUPGHOME=str(home))
env.pop('LD_LIBRARY_PATH', None)
env.pop('LD_PRELOAD', None)
gpg = ['/usr/bin/sailfish-gpg']
conf = [str(prefix / 'bin/gpgconf'), '--homedir', str(home)]
results = {'home': str(home), 'environment': 'SDK target, not phone', 'checks': []}
def run(args, *, data=None):
    result = subprocess.run(args, input=data, text=True, capture_output=True, env=env, timeout=120)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode}): {result.stderr}')
    return result.stdout
def checked(name):
    results['checks'].append(name)
    print('PASS ' + name, flush=True)
try:
    results['version'] = run(gpg + ['--version'])
    results['components'] = run(conf + ['--list-components'])
    results['directories'] = run(conf + ['--list-dirs'])
    assert str(prefix / 'bin/gpg-agent') in results['components']
    checked('private helper paths and explicit home')
    loopback = ['--batch', '--pinentry-mode', 'loopback', '--passphrase-fd', '0']
    run(gpg + loopback + ['--quick-generate-key', 'Synthetic SDK Feasibility <synthetic@example.invalid>', 'ed25519', 'sign', '1d'], data=phrase + '\n')
    keys = run(gpg + ['--with-colons', '--list-keys'])
    fingerprint = next(line.split(':')[9] for line in keys.splitlines() if line.startswith('fpr:'))
    run(gpg + loopback + ['--quick-add-key', fingerprint, 'cv25519', 'encr', '1d'], data=phrase + '\n')
    checked('protected synthetic Ed25519/Cv25519 key generation')
    payload = home / 'payload.txt'
    payload.write_text('Synthetic Sailfish private runtime fixture. No real data.\n')
    encrypted = home / 'payload.gpg'
    run(gpg + ['--batch', '--trust-model', 'always', '--recipient', fingerprint, '--output', str(encrypted), '--encrypt', str(payload)])
    decoded = run(gpg + loopback + ['--decrypt', str(encrypted)], data=phrase + '\n')
    assert decoded == payload.read_text()
    checked('encryption and protected-key loopback decryption')
    run(conf + ['--kill', 'gpg-agent'])
    signature = home / 'payload.sig'
    pid, fd = pty.fork()
    if pid == 0:
        # SDK rules simulate O_CREAT on /dev/pts, but permit /dev/tty. Keep
        # this synthetic agent attached to the controlling PTY for this test.
        env['GPG_TTY'] = '/dev/tty'
        env['TERM'] = 'xterm'
        agent = str(prefix / 'bin/gpg-agent')
        command = [agent, '--homedir', str(home), '--daemon', '--no-detach'] + gpg + ['--output', str(signature), '--detach-sign', str(payload)]
        os.execvpe(agent, command, env)
    transcript = b''
    sent = False
    deadline = time.monotonic() + 120
    child_status = None
    while time.monotonic() < deadline:
        if select.select([fd], [], [], 0.2)[0]:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                chunk = b''
            transcript += chunk
            if not sent and b'passphrase: ' in transcript.lower():
                os.write(fd, (phrase + '\n').encode())
                sent = True
        ended, status = os.waitpid(pid, os.WNOHANG)
        if ended:
            child_status = status
            break
    if child_status is None:
        os.kill(pid, 15)
        os.waitpid(pid, 0)
        raise RuntimeError('TTY pinentry timed out')
    os.close(fd)
    if child_status or not sent or not signature.exists():
        raise RuntimeError('TTY pinentry signing failed: ' + transcript.decode(errors='replace'))
    run(gpg + ['--verify', str(signature), str(payload)])
    checked('real tty pinentry prompt with SDK controlling-tty harness after cache reset; signature verification')
    (home / 'public.asc').write_text(run(gpg + ['--armor', '--export', fingerprint]))
    # Only this synthetic fixture may be used for a later compatibility check.
    checked('export synthetic public fixture')
finally:
    subprocess.run(conf + ['--kill', 'gpg-agent'], env=env, capture_output=True, timeout=30)
    (output / 'runtime-test.json').write_text(json.dumps(results, indent=2) + '\n')

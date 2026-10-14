#!/usr/bin/env python3
"""One keyless native UI/cache smoke using the installed candidate helper."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import selectors
import stat
import subprocess
import sys
import tempfile
import time
from urllib.parse import unquote_to_bytes

assert len(sys.argv) == 2 and sys.argv[1] == 'on-device'
assert os.getuid() == os.geteuid() == 100000
assert os.uname().machine == 'aarch64'
assert 'VERSION_ID=5.2.0.18' in Path('/etc/os-release').read_text()
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
os.umask(0o077)
STAGE = Path(__file__).absolute().parent
assert STAGE.parent == Path('/var/tmp') and STAGE.name.startswith('sailfish-native-vendor.')
info = STAGE.lstat()
assert stat.S_ISDIR(info.st_mode) and info.st_uid == 100000 and stat.S_IMODE(info.st_mode) == 0o700
assert STAGE.resolve() == STAGE
LAUNCH = STAGE / 'native-agent-launch.py'
# Filled and pinned before staging; local source review includes this exact digest.
LAUNCH_HASH = '9b9f8de15c27eb6fc5d5f3055dcbf8f074038013a310e5a2b5325cf1c670b4db'
info = LAUNCH.lstat()
assert stat.S_ISREG(info.st_mode) and info.st_uid == 100000 and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1
assert hashlib.sha256(LAUNCH.read_bytes()).hexdigest() == LAUNCH_HASH
spec = importlib.util.spec_from_file_location('native_launch', LAUNCH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
agent = Path(module.AGENT)
info = agent.lstat()
assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o755
assert hashlib.sha256(agent.read_bytes()).hexdigest() == '78d9721254a2362696ead16e62f77104ad633455c04277eea226df1162c8c1da'
result = subprocess.run(['/usr/bin/rpm', '-q', 'sailfish-gnupg-private'], capture_output=True,
                        env={'PATH':'/usr/bin:/bin','LC_ALL':'C'}, timeout=15)
assert result.returncode == 0 and result.stdout == b'sailfish-gnupg-private-2.5.24-0.3.aarch64\n'
result = subprocess.run(['/usr/bin/rpm', '-V', 'sailfish-gnupg-private'], capture_output=True,
                        env={'PATH':'/usr/bin:/bin','LC_ALL':'C'}, timeout=30)
assert result.returncode == 0 and not result.stdout, 'Private runtime verification failed'
assert not os.path.lexists('/usr/libexec/sailfish-gnupg/bin/gpgconf.ctl'), 'Unexpected relocation configuration'
r = subprocess.run(['/usr/bin/rpm','-q','--qf','%{NAME} %{VERSION}-%{RELEASE} %{ARCH}','sailfishsecretsdaemon-cryptoplugins-gnupg'],capture_output=True,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},timeout=30)
assert r.returncode==0 and r.stdout==b'sailfishsecretsdaemon-cryptoplugins-gnupg 0.2.44-1.14.3.jolla.compat1 aarch64'
r = subprocess.run(['/usr/bin/rpm','-V','sailfishsecretsdaemon-cryptoplugins-gnupg'],capture_output=True,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},timeout=30)
assert r.returncode==0 and not r.stdout, 'Candidate package changed before native proof'
for directory in (Path('/usr/libexec/sailfish-gnupg/etc/gnupg'),):
    for pattern in ('gpg-agent.conf*', 'common.conf*', 'gpgconf.conf*'):
        assert not list(directory.glob(pattern)), 'Unexpected private system configuration'
def no_helper():
    for path in Path('/proc').iterdir():
        if not path.name.isdigit(): continue
        try:
            if path.stat().st_uid != 100000: continue
            name = (path/'comm').read_text().strip()
            if not name.startswith('pinentry'): continue
            assert os.readlink(path/'exe') != str(Path('/usr/bin/pinentry')), 'Known helper still active'
        except FileNotFoundError: continue
no_helper()
assert not os.path.lexists(STAGE/'cache-attempt.json'), 'Prior attempt must be preserved, no repeat'
fixture = Path(tempfile.mkdtemp(prefix='synthetic-native-cache-', dir='/var/tmp'))
home = fixture / 'gnupg'
home.mkdir(mode=0o700)
(fixture / '.synthetic-fixture').write_bytes(b'native-agent-cache-lifecycle-v1\n')
argv = module.checked_argv(home, Path('/usr/bin/pinentry'))
record = {'fixture': str(fixture), 'agent_argv': argv, 'human_launch_attestation': 'on-device',
          'scope': 'one installed candidate native helper keyless cold/warm RPC; no crypto/provider-discovery/lock observer', 'events': [], 'agents': [], 'complete': False}
STATE = STAGE / 'cache-attempt.json'
with STATE.open('x') as f:
    json.dump(record, f); f.flush(); os.fsync(f.fileno())

def save():
    with tempfile.NamedTemporaryFile(mode='w', dir=STAGE, delete=False) as f:
        json.dump(record, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno()); name = f.name
    os.replace(name, STATE)
    fd = os.open(STAGE, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

env = {'PATH': '/usr/bin:/bin', 'HOME': str(home), 'GNUPGHOME': str(home),
       'LANG': 'C', 'LC_ALL': 'C', 'XDG_RUNTIME_DIR': '/run/user/100000',
       'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/100000/bus', 'QT_LOGGING_RULES': '*.debug=false'}
request = 'GET_PASSPHRASE --data SYNTHETIC-NATIVE-CACHE X Synthetic Synthetic+cache+test'
noask = request.replace('--data ', '--data --no-ask ', 1)
for generation in (1,):
    no_helper()
    record['pending_launch'] = generation; save()
    with tempfile.TemporaryFile() as log:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, env=env)
        ident = {'generation': generation, 'pid': proc.pid, 'reaped': False}
        try:
            record['agents'].append(ident); record.pop('pending_launch', None); save()
            path = Path('/proc') / str(proc.pid)
            assert path.stat().st_uid == 100000
            deadline = time.monotonic() + 3
            while True:
                actual = (path / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
                if actual and actual[0] == module.AGENT.encode(): break
                assert time.monotonic() < deadline, 'Agent exec identity not ready'
                time.sleep(0.02)
            assert module.policy_matches([v.decode() for v in actual], home, Path('/usr/bin/pinentry'))
            assert os.readlink(path/'exe') == module.AGENT
            ident['start'] = (path / 'stat').read_text().split(') ', 1)[1].split()[19]; save()
            selector = selectors.DefaultSelector(); selector.register(proc.stdout, selectors.EVENT_READ)
            buffer = bytearray()
            def reply(seconds=90):
                deadline = time.monotonic() + seconds; data = bytearray()
                while True:
                    while b'\n' in buffer:
                        line, _, tail = buffer.partition(b'\n'); buffer[:] = tail; line = line.rstrip(b'\r')
                        if line.startswith(b'D '):
                            data.extend(unquote_to_bytes(line[2:])); assert len(data) <= 64
                        elif line.startswith(b'OK') or line.startswith(b'ERR '):
                            return (int(line.split()[1]) & 65535 if line.startswith(b'ERR ') else 0), bytes(data)
                    left = deadline - time.monotonic(); assert left > 0 and selector.select(left), 'RPC deadline exceeded'
                    block = os.read(proc.stdout.fileno(), 4096); assert block, 'Agent closed without reply'
                    buffer.extend(block); assert len(buffer) <= 65536
            assert reply(15) == (0, b'')
            maps = (path/'maps').read_text()
            for library in ('libassuan', 'libgcrypt', 'libgpg-error', 'libnpth'):
                entries = [line.split()[-1] for line in maps.splitlines() if '/'+library+'.so' in line]
                assert entries and all(v.startswith('/usr/libexec/sailfish-gnupg/lib/') for v in entries)
            ident['startup_policy_verified'] = True
            def command(text, label):
                record['pending_operation'] = label; save()
                assert text in (request, noask, 'BYE'), 'RPC outside fixed synthetic whitelist'
                proc.stdin.write(text.encode() + b'\n'); proc.stdin.flush()
                code, data = reply()
                record['events'].append({'generation': generation, 'label': label, 'error': code,
                                         'data_bytes': len(data), 'synthetic_bytes_match': data == b'test-123'})
                record.pop('pending_operation', None); save()
                return code, data
            assert command(noask, 'initial-cache-miss') == (58, b'')
            print('Native cache test: enter test-123 (generation %d).' % generation, flush=True)
            assert command(request, 'cold-prompt') == (0, b'test-123')
            assert command(noask, 'warm-noask') == (0, b'test-123')
            assert command('BYE', 'stop') == (0, b'')
            proc.stdin.close(); assert proc.wait(timeout=10) == 0
            ident['reaped'] = True; save()
            no_helper()
            selector.close()
        finally:
            if proc.returncode is None:
                proc.terminate()
                try: proc.wait(timeout=10)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
                ident['reaped'] = True; record['failure_cleanup'] = True
                try:
                    no_helper(); ident['helper_absence_after_failure'] = True
                except (AssertionError, OSError):
                    ident['helper_absence_after_failure'] = False
                save()
record['complete'] = True; save()
print('PASS: installed candidate native cold/warm smoke; owned agent reaped. Fixture retained.', flush=True)

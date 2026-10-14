#!/usr/bin/env python3
"""Pure launch-policy construction for an isolated synthetic native agent.

No process launch, configuration read, socket access or production installation.
"""
from pathlib import Path
import hashlib
import os
import stat

AGENT = '/usr/libexec/sailfish-gnupg/bin/gpg-agent'
HELPER_SHA256 = '23cdd69adcc4a37ed0916cab3818e194f9a5add50668c5e57494c930d3bbc3fb'
IDLE_TTL = 300
MAX_TTL = 900


def checked_argv(home: Path, helper: Path, uid: int = 100000):
    """Validate only a fresh marked synthetic home and pinned public helper."""
    if os.getuid() != uid or os.geteuid() != uid:
        raise ValueError('Wrong execution identity')
    home = Path(home)
    helper = Path(helper)
    fixture = home.parent
    if (not home.is_absolute() or home.name != 'gnupg'
            or fixture.parent != Path('/var/tmp')
            or not fixture.name.startswith('synthetic-native-cache-')):
        raise ValueError('Outside synthetic fixture scope')
    for path in (fixture, home):
        info = path.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != uid
                or stat.S_IMODE(info.st_mode) != 0o700
                or path.resolve() != path):
            raise ValueError('Unsafe synthetic directory')
    marker = fixture / '.synthetic-fixture'
    info = marker.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != uid
            or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600
            or marker.read_bytes() != b'native-agent-cache-lifecycle-v1\n'):
        raise ValueError('Missing exact synthetic provenance')
    # A keyless test does not permit preexisting keys or configuration.
    if any(home.iterdir()):
        raise ValueError('Synthetic home must be empty before first launch')
    if helper != Path('/usr/bin/pinentry') or helper.resolve() != helper:
        raise ValueError('Unsafe helper path')
    info = helper.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
            or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o755
            or hashlib.sha256(helper.read_bytes()).hexdigest() != HELPER_SHA256):
        raise ValueError('Native helper does not match reviewed artifact')
    return [AGENT, '--homedir', str(home), '--no-options',
            '--disable-scdaemon', '--pinentry-program', str(helper),
            '--no-allow-external-cache', '--default-cache-ttl', str(IDLE_TTL),
            '--max-cache-ttl', str(MAX_TTL), '--server']


def policy_matches(actual_argv, home, helper):
    """Require exact process arguments; command-line evidence is startup-only."""
    expected = [AGENT, '--homedir', str(home), '--no-options',
                '--disable-scdaemon', '--pinentry-program', str(helper),
                '--no-allow-external-cache', '--default-cache-ttl', str(IDLE_TTL),
                '--max-cache-ttl', str(MAX_TTL), '--server']
    return actual_argv == expected

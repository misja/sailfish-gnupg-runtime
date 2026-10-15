#!/usr/bin/python3 -I
"""Fixed-path runtime entry. No caller-selected state or helper paths.

Operation supervision and agent watches are separate processes. This does not
implement package-generation authentication, recovery or process quiescence.
"""
import os
import fcntl
from pathlib import Path
import select
import signal
import stat
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lifecycle_admission import Admission, AdmissionError

PREFIX = Path('/usr/libexec/sailfish-gnupg')
STATE = Path('/var/lib/sailfish-gnupg-runtime')


def identity(pid):
    """Public process identity only; never argv, environment or key data."""
    info = Path('/proc') / str(pid)
    content = (info / 'stat').read_text()
    fields = content.rsplit(') ', 1)[1].split()
    if len(fields) < 20:
        raise AdmissionError('Invalid process identity')
    return info.stat().st_uid, fields[19], fields[0]


def watch(pid, start, uid, interval=0.2):
    while True:
        try:
            actual_uid, actual_start, state = identity(pid)
            if (actual_uid, actual_start) != (uid, start) or state == 'Z':
                return
        except FileNotFoundError:
            return
        except (OSError, ValueError, IndexError, AdmissionError):
            # Uncertainty retains registration; never assume the agent exited.
            pass
        time.sleep(interval)


class Runtime:
    def __init__(self, admission=None, prefix=PREFIX):
        # Explicit injection is for tests, never parsed from argv/environment.
        self.admission = admission if admission is not None else Admission(STATE)
        self.prefix = Path(prefix)
        self.monitors = []

    def _monitor(self, registration, pid, start):
        home = Path(os.environ.get('SAILFISH_GNUPGHOME', ''))
        if not home.is_absolute() or home.resolve(strict=True) != home:
            raise AdmissionError('Private home must be canonical')
        directory = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            info = os.fstat(directory)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
                raise AdmissionError('Unsafe private-home metadata directory')
            # Stable identity-specific lock: never unlink it while another
            # caller may have it open. Contains no key/configuration material.
            name = '.sailfish-agent-watch-' + registration.generation + '-' + str(pid) + '-' + start + '.lock'
            watch_fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                               0o600, dir_fd=directory)
        finally:
            os.close(directory)
        try:
            info = os.fstat(watch_fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
                raise AdmissionError('Unsafe agent-watch metadata lock')
            try:
                fcntl.flock(watch_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                # A cooperating watcher for this exact home/generation/PID/
                # start identity already owns the registration.
                os.close(watch_fd)
                return
            child = os.fork()
        except BaseException:
            os.close(watch_fd)
            raise
        if child != 0:
            os.close(watch_fd)
        if child == 0:
            try:
                os.setsid()
                # The detached watcher must not keep the operation lease, the
                # reporting pipe, user terminal, or any other inherited FD.
                agent_copy = fcntl.fcntl(registration.fd, fcntl.F_DUPFD_CLOEXEC, 10)
                watch_copy = fcntl.fcntl(watch_fd, fcntl.F_DUPFD_CLOEXEC, 10)
                os.dup2(agent_copy, 3, inheritable=True)
                os.dup2(watch_copy, 4, inheritable=True)
                # Enumerate only this process's descriptor numbers, never
                # contents, so high-numbered inherited leases cannot leak.
                for name in os.listdir('/proc/self/fd'):
                    fd = int(name)
                    if fd > 4:
                        try:
                            os.close(fd)
                        except OSError:
                            # listdir's own descriptor is already closed.
                            pass
                null = os.open('/dev/null', os.O_RDWR)
                for fd in (0, 1, 2):
                    os.dup2(null, fd)
                if null > 4:
                    os.close(null)
                watch(pid, start, os.getuid())
                os._exit(0)
            except BaseException:
                # A watcher error must retain its registration rather than
                # silently announce agent absence. Operator recovery is pending.
                while True:
                    time.sleep(60)
        self.monitors.append(child)
        registration.close()

    def run(self, role, arguments):
        if role not in {'gpg', 'agent'}:
            raise AdmissionError('Unknown runtime entry point')
        if role == 'agent' and (len(arguments) != 1 or arguments[0] not in {'status', 'start', 'stop'}):
            return 64
        stopping = role == 'agent' and arguments == ['stop']
        lease = self.admission.acquire_stop() if stopping else self.admission.acquire()
        with lease:
            command = ['/usr/bin/busybox', 'sh', str(self.prefix / 'libexec' / (role + '-operation'))] + arguments
            if stopping:
                child = lease.spawn(command)
                result = child.wait()
                return result if result >= 0 else 128 - result
            read_fd, write_fd = os.pipe()
            environment = dict(os.environ)
            environment['SAILFISH_LIFECYCLE_REPORT_FD'] = str(write_fd)
            try:
                child = subprocess.Popen(command, env=environment, pass_fds=(lease.fd, write_fd))
            except BaseException:
                os.close(read_fd)
                os.close(write_fd)
                raise
            os.close(write_fd)
            report = b''
            try:
                # The fixed shell reports before exec, or closes the descriptor
                # at exit. Never read the operation's stdin/stdout as metadata.
                while b'\n' not in report and len(report) <= 128:
                    ready, _, _ = select.select([read_fd], [], [], 0.2)
                    if ready:
                        data = os.read(read_fd, 129 - len(report))
                        if not data:
                            break
                        report += data
                    elif child.poll() is not None:
                        break
                valid = False
                if report == b'absent\n' and role == 'gpg':
                    valid = True
                elif report:
                    fields = report.decode('ascii').strip().split()
                    if len(fields) != 2 or not all(value.isdigit() for value in fields):
                        raise AdmissionError('Invalid agent identity report')
                    pid, start = int(fields[0]), fields[1]
                    uid, actual_start, state = identity(pid)
                    if uid != os.getuid() or start != actual_start or state == 'Z':
                        raise AdmissionError('Agent identity changed before registration')
                    registration = self.admission.acquire_agent(lease)
                    try:
                        self._monitor(registration, pid, start)
                    finally:
                        registration.close()
                    valid = True
                result = child.wait()
                passive = role == 'gpg' and arguments in (['--version'], ['--help'], ['--dump-options'])
                if result == 0 and not valid and not passive:
                    return 78
                return result if result >= 0 else 128 - result
            finally:
                os.close(read_fd)
                # Retain the operation registration through child termination,
                # including failure while parsing/registering its agent report.
                child.wait()


def main(argv):
    if not argv or argv[0] not in {'gpg', 'agent'}:
        return 64
    # The public calling wrapper can disappear without releasing registration:
    # a separate guardian owns the lease and the actual operation child.
    guardian = os.fork()
    if guardian == 0:
        # Keep registration until the operation exits, even when terminal or
        # calling-wrapper signals interrupt the guardian's wait. Caught signal
        # handlers reset to default on the operation child's exec.
        for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(number, lambda unused_number, unused_frame: None)
        try:
            result = Runtime().run(argv[0], argv[1:])
        except BlockingIOError:
            print('Private runtime is busy; retry after the active operation', file=sys.stderr)
            result = 75
        except (AdmissionError, OSError, ValueError):
            print('Private runtime lifecycle state or agent registration is unavailable', file=sys.stderr)
            result = 78
        os._exit(result)
    _, status = os.waitpid(guardian, 0)
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    return 128 + os.WTERMSIG(status)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

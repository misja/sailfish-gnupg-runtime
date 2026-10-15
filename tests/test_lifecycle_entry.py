"""Public wrappers against explicit temporary copies and inert child/agent stubs.

Only test copies replace fixed prefix/state/owner constants. Installed scripts
have no path/UID override through their environment or command-line interface.
"""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from lifecycle_admission import Admission, AdmissionError
from lifecycle_control import Payload


def start_identity(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()[19]


@unittest.skipUnless(Path('/usr/bin/busybox').is_file(), 'BusyBox required')
class LifecycleEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-entry-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prefix = self.root / 'private'
        self.libexec = self.prefix / 'libexec'
        self.libexec.mkdir(parents=True)
        self.state = self.root / 'state'
        self.gate = Admission(self.state, expected_uid=os.geteuid())
        self.gate.initialize('b' * 64)
        self.agent = subprocess.Popen([sys.executable, '-I', '-c', 'import time; time.sleep(60)'])
        self.addCleanup(self.stop_agent)
        self.start = start_identity(self.agent.pid)
        self.report = f'{self.agent.pid} {self.start}'
        (self.root / 'synthetic-home').mkdir(mode=0o700)
        self.environment = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C',
                            'SAILFISH_GNUPGHOME': str(self.root / 'synthetic-home')}
        entry = (ROOT / 'runtime/lifecycle-entry.py').read_text()
        entry = entry.replace("PREFIX = Path('/usr/libexec/sailfish-gnupg')", f'PREFIX = Path({str(self.prefix)!r})')
        entry = entry.replace("STATE = Path('/var/lib/sailfish-gnupg-runtime')", f'STATE = Path({str(self.state)!r})')
        entry = entry.replace('Admission(STATE)', 'Admission(STATE, expected_uid=os.getuid())')
        entry = entry.replace('Payload(PREFIX)', 'Payload(PREFIX, entrypoints=(PREFIX.parent / \"sailfish-gpg\", PREFIX.parent / \"sailfish-gpg-agent\"), expected_uid=os.getuid())')
        (self.libexec / 'lifecycle-entry.py').write_text(entry)
        (self.libexec / 'lifecycle_admission.py').write_bytes((ROOT / 'runtime/lifecycle_admission.py').read_bytes())
        (self.libexec / 'lifecycle_control.py').write_bytes((ROOT / 'runtime/lifecycle_control.py').read_bytes())
        for name in ('sailfish-gpg', 'sailfish-gpg-agent'):
            text = (ROOT / 'runtime' / name).read_text().replace('/usr/libexec/sailfish-gnupg', str(self.prefix)).replace('/var/lib/sailfish-gnupg-runtime', str(self.state))
            (self.root / name).write_text(text)
        self.operation("printf 'completed\\n'")
        self.agent_operation()

    def stop_agent(self):
        if self.agent.poll() is None:
            self.agent.terminate()
        self.agent.wait(timeout=3)
        # Watches are separate sessions. Let them close their registration
        # themselves after their one explicitly owned inert agent exits.
        deadline = time.monotonic() + 3
        while self.state.exists() and self.gate.agents_registered():
            self.assertLess(time.monotonic(), deadline, 'Agent watch retained registration')
            time.sleep(0.02)

    def operation(self, body, report=True):
        prefix = f"printf '{self.report}\\n' >&\"$SAILFISH_LIFECYCLE_REPORT_FD\"\n" if report else ''
        (self.libexec / 'gpg-operation').write_text('#!/usr/bin/busybox sh\nset -eu\n' + prefix + body + '\n')

    def agent_operation(self):
        (self.libexec / 'agent-operation').write_text(
            '#!/usr/bin/busybox sh\nset -eu\n'
            f'if test "$1" = stop; then kill -TERM {self.agent.pid}; exit 0; fi\n'
            f'printf \'{self.report}\\n\' >&"$SAILFISH_LIFECYCLE_REPORT_FD"\n'
            "printf 'managed agent\\n'\n")

    def invoke(self, *arguments, agent=False, refresh=True, **kwargs):
        # Fixture code is deliberately rewritten by individual tests; establish
        # its manifest and bind the fixture state explicitly before execution.
        if refresh:
            self.prefix.chmod(0o755)
            for path in self.prefix.rglob('*'):
                path.chmod(0o755 if path.is_dir() else 0o644)
            for name in ('sailfish-gpg', 'sailfish-gpg-agent'):
                (self.root / name).chmod(0o644)
            payload = Payload(self.prefix, entrypoints=(self.root / 'sailfish-gpg', self.root / 'sailfish-gpg-agent'), expected_uid=os.geteuid())
            generation = payload.build_manifest()
            try:
                with self.gate._directory() as directory, self.gate._gate(directory, exclusive=True):
                    state = self.gate._read(directory)
                    if state['state'] == 'ACTIVE':
                        self.gate._write(directory, state['state'], generation)
            except FileNotFoundError:
                pass
        command = ['/usr/bin/busybox', 'sh', str(self.root / ('sailfish-gpg-agent' if agent else 'sailfish-gpg'))] + list(arguments)
        process = subprocess.Popen(command, env=self.environment, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=True, **kwargs)
        def cleanup():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=3)
        self.addCleanup(cleanup)
        return process

    def finish(self, process, expected=0):
        output, error = process.communicate(timeout=5)
        self.assertEqual(process.returncode, expected, error)
        return output

    def ready(self, process):
        import select
        self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'No operation readiness marker')
        self.assertEqual(process.stdout.readline().strip(), 'READY')

    def wait_agent_registration(self):
        deadline = time.monotonic() + 3
        while not self.gate.agents_registered():
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.02)

    def test_completed_client_leaves_agent_registered_separately(self):
        self.assertEqual(self.finish(self.invoke()), 'completed\n')
        self.assertEqual(self.gate.drain(0), 'DRAINED')
        self.assertTrue(self.gate.agents_registered())
        self.finish(self.invoke(), 78)
        self.finish(self.invoke('stop', agent=True))
        self.stop_agent()
        self.assertFalse(self.gate.agents_registered())
        self.assertEqual(self.gate.status()['state'], 'DRAINED')

    def interrupted_operation(self, number):
        self.operation("exec /usr/bin/python3 -I -c 'import os,time; os.closerange(3,1024); print(\"READY\",flush=True); time.sleep(30)'")
        caller = self.invoke()
        self.ready(caller)
        self.wait_agent_registration()
        caller.send_signal(number)
        caller.wait(timeout=3)
        self.assertEqual(self.gate.drain(0), 'BLOCKED')

    def test_public_wrapper_kill_keeps_operation_registration_after_child_closes_fds(self):
        self.interrupted_operation(signal.SIGKILL)

    def test_public_wrapper_term_keeps_operation_registration_after_child_closes_fds(self):
        self.interrupted_operation(signal.SIGTERM)

    def test_repeated_calls_share_one_stable_watch_lock(self):
        self.finish(self.invoke())
        home = self.root / 'synthetic-home'
        locks = list(home.glob('.sailfish-agent-watch-*.lock'))
        self.assertEqual(len(locks), 1)
        inode = locks[0].stat().st_ino
        # The existing exclusive lock is held by the detached watcher.
        import fcntl
        with locks[0].open('rb') as stream:
            with self.assertRaises(BlockingIOError):
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.finish(self.invoke())
        self.assertEqual(list(home.glob('.sailfish-agent-watch-*.lock')), locks)
        self.assertEqual(locks[0].stat().st_ino, inode)
        self.assertTrue(self.gate.agents_registered())

    def test_stop_rejects_active_operation(self):
        self.operation("exec /usr/bin/python3 -I -c 'import time; print(\"READY\",flush=True); time.sleep(30)'")
        caller = self.invoke()
        self.ready(caller)
        self.finish(self.invoke('stop', agent=True), 75)
        self.assertIsNone(self.agent.poll())

    def test_agent_start_registers_persistent_lifetime(self):
        self.assertEqual(self.finish(self.invoke('start', agent=True)), 'managed agent\n')
        self.assertTrue(self.gate.agents_registered())

    def test_passive_version_does_not_start_or_register_agent(self):
        self.operation("printf 'version fixture\\n'", report=False)
        self.assertEqual(self.finish(self.invoke('--version')), 'version fixture\n')
        self.assertFalse(self.gate.agents_registered())

    def test_explicit_absent_agent_report_needs_no_agent_registration(self):
        self.operation("printf 'absent\\n' >&\"$SAILFISH_LIFECYCLE_REPORT_FD\"; exit 0", report=False)
        self.finish(self.invoke('--no-autostart', '--list-keys'))
        self.assertFalse(self.gate.agents_registered())

    def test_successful_operation_without_identity_report_is_rejected(self):
        self.operation('exit 0', report=False)
        self.finish(self.invoke('--list-keys'), 78)

    def test_report_with_wrong_start_identity_is_rejected(self):
        self.report = f'{self.agent.pid} 0'
        self.operation('exit 0')
        self.finish(self.invoke(), 78)
        self.assertFalse(self.gate.agents_registered())

    def test_environment_cannot_reopen_closed_admission(self):
        self.gate.drain(0)
        self.environment.update({'SAILFISH_LIFECYCLE_STATE': '/tmp/unused', 'PYTHONPATH': '/tmp/unused',
                                 'SAILFISH_LIFECYCLE_REPORT_FD': '1'})
        self.finish(self.invoke(), 78)

    def test_missing_state_fails_before_operation_exec(self):
        (self.state / 'state.json').unlink()
        process = self.invoke()
        self.assertEqual(self.finish(process, 78), '')

    def test_bootstrap_lock_is_taken_before_private_python_is_parsed(self):
        import fcntl
        fd = os.open(self.state / 'bootstrap.lock', os.O_RDONLY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            (self.libexec / 'lifecycle-entry.py').write_text('deliberately invalid Python @@@')
            self.finish(self.invoke(), 75)
        finally:
            os.close(fd)

    def test_changed_payload_is_rejected_before_operation_execution(self):
        self.operation("printf 'passive\\n'", report=False)
        self.finish(self.invoke('--version'))
        (self.libexec / 'gpg-operation').write_text("printf 'must not execute\\n'\n")
        self.assertEqual(self.finish(self.invoke('--version', refresh=False), 78), '')

    def test_invalid_agent_action_is_rejected(self):
        self.finish(self.invoke('unknown', agent=True), 64)


if __name__ == '__main__':
    unittest.main()
